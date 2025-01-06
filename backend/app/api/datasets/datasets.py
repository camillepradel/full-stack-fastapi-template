import logging
from dataclasses import dataclass
from pathlib import Path

import kuzu

from app.models import (
    Dataset,
    DatasetContent,
    DatasetFilters,
    DatasetPublic,
    FilterSelect,
    GraphElementFilter,
    Node,
    NodeType,
    Relation,
    RuleGroup,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _id_dict_to_str(id_dict: dict[str, int]) -> str:
    return f"{id_dict['offset']}_{id_dict['table']}"


@dataclass
class QueryConstraintsGroup:
    combinator: str
    constraints: list["QueryConstraintsGroup|str"]

    def __str__(self):
        if len(self.constraints) == 0:
            return ""
        elif len(self.constraints) == 1:
            return str(self.constraints[0])
        else:
            return (
                "("
                + f" {self.combinator} ".join(
                    [str(constraint) for constraint in self.constraints]
                )
                + ")"
            )


def _get_rule_group_constraints_on_node(
    rule_group: RuleGroup, node_type: NodeType
) -> QueryConstraintsGroup:
    def _format_rule_value(rule, node_type: NodeType):
        property = next(
            (prop for prop in node_type.properties if prop.name == rule.field), None
        )
        if property and property.type == "STRING":
            return f"'{rule.value}'"
        else:
            return rule.value

    return QueryConstraintsGroup(
        combinator=rule_group.combinator.upper(),
        constraints=[
            f"__NODE__.{rule.field} {rule.operator} {_format_rule_value(rule, node_type)}"
            for rule in rule_group.rules
        ],
    )


def _get_filters_constraints_on_node(
    dataset: Dataset, filters: DatasetFilters
) -> QueryConstraintsGroup:
    result = QueryConstraintsGroup(combinator="OR", constraints=[])
    constraining_node_filters: list[GraphElementFilter] = [
        filter
        for filter in filters.node_filters
        if filter.select != FilterSelect.everything
    ]
    if len(constraining_node_filters) == 0:
        return result
    for node_type in dataset.dataset_schema.node_types:
        node_filter: GraphElementFilter | None = next(
            (
                filter
                for filter in constraining_node_filters
                if filter.element_type_name == node_type.name
            ),
            None,
        )
        if not node_filter:
            result.constraints.append(f"LABEL(__NODE__)='{node_type.name}'")
        elif node_filter.select == FilterSelect.nothing:
            # nodes of type node_type.name will be filtered out
            continue
        else:
            # node_filter.select is custom -> we take into account filter_value
            result.constraints.append(
                QueryConstraintsGroup(
                    combinator="AND",
                    constraints=[
                        f"LABEL(__NODE__)='{node_type.name}'",
                        _get_rule_group_constraints_on_node(
                            node_filter.filter_value, node_type
                        ),
                    ],
                )
            )
    return result


def read_dataset_from_kuzu(
    dataset: Dataset,
    filters: DatasetFilters,
    limit: int | None = None,
) -> DatasetContent:
    # Initialize database
    db_path: Path = Path(dataset.kuzu_path)
    if not (db_path.exists() and db_path.is_dir()):
        raise RuntimeError("Specified dataset does not exist.")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    logger.info("retrieve content")
    query: str = "MATCH (n1)\n"
    constraints_on_nodes: QueryConstraintsGroup = _get_filters_constraints_on_node(
        dataset, filters
    )
    if constraints_on_nodes.constraints:
        query += "WHERE\n(\n"
        query += str(constraints_on_nodes).replace("__NODE__", "n1")
        query += "\n)\n"
    query += "OPTIONAL MATCH (n1)-[r]->(n2)\n"
    if constraints_on_nodes.constraints:
        query += "WHERE\n(\n"
        query += str(constraints_on_nodes).replace("__NODE__", "n2")
        query += "\n)\n"
    query += "RETURN *\n"
    if limit:
        query += f"LIMIT {limit}\n"
    result = conn.execute(query)
    nodes: list[Node] = []
    node_ids: set[str] = set()
    df = result.get_as_df()
    relations: list[Relation] = []
    for _, row in df.iterrows():
        # read nodes
        for node_name in ["n1", "n2"]:
            node_data = row[node_name]
            if not isinstance(
                node_data, float
            ):  # n2 can be nan beacause of optional match
                node_id = _id_dict_to_str(node_data.pop("_id"))
                if node_id not in node_ids:
                    node_ids.add(node_id)
                    node_type = node_data.pop("_label")
                    nodes.append(
                        Node(
                            id=node_id,
                            type=node_type,
                            data=node_data,
                        )
                    )
        # read relation
        relation_data = row["r"]
        if not isinstance(
            relation_data, float
        ):  # r can be nan beacause of optional match
            relation_source_id = _id_dict_to_str(relation_data.pop("_src"))
            relation_target_id = _id_dict_to_str(relation_data.pop("_dst"))
            relation_type = relation_data.pop("_label")
            relations.append(
                Relation(
                    source=relation_source_id,
                    target=relation_target_id,
                    type=relation_type,
                    data=relation_data,
                )
            )

    dataset_content = DatasetContent(
        metadata=DatasetPublic.model_validate(dataset), relations=relations, nodes=nodes
    )

    return dataset_content
