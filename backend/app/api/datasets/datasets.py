import logging
from pathlib import Path

import kuzu

from app.models import (
    Dataset,
    DatasetContent,
    DatasetPublic,
    Node,
    Relation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _id_dict_to_str(id_dict: dict[str, int]) -> str:
    return f"{id_dict['offset']}_{id_dict['table']}"


def read_dataset_from_kuzu(
    dataset: Dataset,
) -> DatasetContent:
    # Initialize database
    db_path: Path = Path(dataset.kuzu_path)
    if not (db_path.exists() and db_path.is_dir()):
        raise RuntimeError("Specified dataset does not exist.")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    logger.info("retrieve all relations")
    result = conn.execute("MATCH ()-[r]->() RETURN *;")
    df = result.get_as_df()
    relations: list[Relation] = []
    for _, row in df.iterrows():
        relation_data = row["r"]
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

    logger.info("retrieve all nodes")
    result = conn.execute("MATCH (n) RETURN *;")
    df = result.get_as_df()
    nodes: list[Node] = []
    for _, row in df.iterrows():
        node_data = row["n"]
        node_id = _id_dict_to_str(node_data.pop("_id"))
        node_type = node_data.pop("_label")
        nodes.append(
            Node(
                id=node_id,
                type=node_type,
                data=node_data,
            )
        )

    dataset_content = DatasetContent(
        metadata=DatasetPublic.model_validate(dataset), relations=relations, nodes=nodes
    )

    return dataset_content
