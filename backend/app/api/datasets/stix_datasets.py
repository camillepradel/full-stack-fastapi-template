import logging
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

import kuzu
import numpy as np
import pandas as pd
import stix2

from app.models import (
    Dataset,
    StixDatasetSpecifications,
)

_T = TypeVar("_T")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO: merge with other batch() functions
def batch(iterable: list[_T], n: int = 1) -> Iterable[list[_T]]:
    iterable_length = len(iterable)
    for ndx in range(0, iterable_length, n):
        yield iterable[ndx : min(ndx + n, iterable_length)]


def stix_to_kuzu_relation_type(rel_type: str) -> str:
    return rel_type.replace("-", "_")


STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE = {
    # full list of stix2 properties: https://stix2.readthedocs.io/en/latest/api/stix2.properties.html
    # TODO: support all types
    stix2.properties.BooleanProperty: ("BOOLEAN", np.bool_),
    stix2.properties.FloatProperty: ("FLOAT", np.float32),
    stix2.properties.IDProperty: ("STRING", np.string_),
    stix2.properties.IntegerProperty: ("INT32", np.int32),
    stix2.properties.StringProperty: ("STRING", np.string_),
    stix2.properties.TimestampProperty: ("TIMESTAMP", np.datetime64),
}


def _stix_objects_to_nodes_df(stix_objects) -> pd.DataFrame:
    nodes_list = []
    for stix_object in stix_objects:
        if stix_object.type != "relationship":
            node_dict = {
                property_name: property_value
                for (property_name, property_value) in stix_object.items()
                if type(stix_object._properties[property_name])
                in STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE
            }
            node_dict["type"] = type(stix_object)
            nodes_list.append(node_dict)
    return pd.DataFrame(nodes_list)


def _stix_objects_to_relations_df(stix_objects, nodes) -> pd.DataFrame:
    nodes_list = []
    for stix_object in stix_objects:
        # only add relations whose nodes were kept during sampling
        if (
            stix_object.type == "relationship"
            and (nodes.id == stix_object.source_ref).any()
            and (nodes.id == stix_object.target_ref).any()
        ):
            node_dict = {
                "f": stix_object.source_ref,
                "t": stix_object.target_ref,
                "source_type": nodes[nodes.id == stix_object.source_ref].iloc[0].type,
                "target_type": nodes[nodes.id == stix_object.target_ref].iloc[0].type,
            }
            node_dict.update(
                {
                    property_name: stix_object.__getattr__(property_name)
                    if property_name in stix_object
                    else None
                    for property_name, property in stix2.Relationship._properties.items()
                    if type(property) in STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE
                }
            )
            nodes_list.append(node_dict)
    relations = pd.DataFrame(nodes_list)
    return relations


def _get_relation_name(relationship_type, source_type, target_type) -> str:
    return f"{source_type.__name__}_{stix_to_kuzu_relation_type(relationship_type)}_{target_type.__name__}"


def instanciate_dataset_in_kuzu(
    dataset: Dataset, specifications: StixDatasetSpecifications
):
    # TODO: move below setup lines to a common decorator @setup_kuzu_connection and use
    #       it in all instanciate_dataset_in_kuzu() functions

    assert isinstance(specifications, StixDatasetSpecifications)
    # Initialize database
    db_path: Path = Path(dataset.kuzu_path)
    if db_path.exists() and db_path.is_dir():
        raise RuntimeError("Path specified for DB already exists. Abort DB creation.")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    stix_data = stix2.parse(specifications.file_content)

    nodes: pd.DataFrame = _stix_objects_to_nodes_df(stix_data.objects)
    if dataset.sampling_count is not None or dataset.sampling_ratio is not None:
        nodes = nodes.sample(
            n=dataset.sampling_count,
            frac=dataset.sampling_ratio,
        )

    # get list of properties for each type from stix2 library (and not from the data) to allow for adding more data with unseen properties
    all_node_types = list(nodes.type.unique())
    type_to_properties = {
        stix_type: [
            (property_name, STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE[type(property)][0])
            for property_name, property in stix_type._properties.items()
            if type(property) in STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE
        ]
        for stix_type in all_node_types
    }

    logger.info(f"create {len(all_node_types)} node classes")
    statement = ""
    for stix_type, properties in type_to_properties.items():
        statement += f"CREATE NODE TABLE {stix_type.__name__}({', '.join(property_name + ' ' + property_type for (property_name, property_type) in properties)}, PRIMARY KEY (id));\n"
    conn.execute(statement)

    for stix_type in type_to_properties.keys():
        class_name: str = stix_type.__name__
        logger.info(f"create all node instances of type {class_name}")
        typenodes = nodes[nodes.type == stix_type]  # noqa: F841
        typenodes = typenodes.drop("type", axis=1)
        typenodes = typenodes.dropna(axis=1, how="all")
        # to generate statement, we use typenodes.columns (and not properties from type_to_properties) to make sure there are no reference to absent columns
        statement = (
            "LOAD FROM typenodes CREATE (n:"
            + class_name
            + " {"
            + ", ".join(column + ": " + column for column in typenodes.columns)
            + "});"
        )
        conn.execute(statement)

    all_relation_types = list(
        {
            (
                stix_rel.relationship_type,
                nodes[nodes.id == stix_rel.source_ref].iloc[0].type,
                nodes[nodes.id == stix_rel.target_ref].iloc[0].type,
            )
            for stix_rel in stix_data.objects
            if stix_rel.type == "relationship"
        }
    )

    logger.info("create relation types")
    # TODO?: use relationship table group (https://docs.kuzudb.com/cypher/data-definition/create-table/#create-relationship-table-group)
    relation_properties = {
        property_name: STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE[type(property)][0]
        for property_name, property in stix2.Relationship._properties.items()
        if type(property) in STIX_TO_KUZU_AND_PANDAS_PROPERTY_TYPE
    }
    properties_in_create_statement: str = ", ".join(
        property_name + " " + property_type
        for property_name, property_type in relation_properties.items()
    )
    statement = ""
    for relationship_type, source_type, target_type in all_relation_types:
        statement += f"CREATE REL TABLE {_get_relation_name(relationship_type, source_type, target_type)} (FROM {source_type.__name__} TO {target_type.__name__}, {properties_in_create_statement});\n"
    conn.execute(statement)

    relations: pd.DataFrame = _stix_objects_to_relations_df(stix_data.objects, nodes)
    for relationship_type, source_type, target_type in all_relation_types:
        relation_name = _get_relation_name(relationship_type, source_type, target_type)
        logger.info(f"create relation triples of type {relation_name}")
        type_relations = relations[
            (relations.relationship_type == relationship_type)
            & (relations.source_type == source_type)
            & (relations.target_type == target_type)
        ]  # noqa: F841
        type_relations = type_relations.drop("source_type", axis=1)
        type_relations = type_relations.drop("target_type", axis=1)
        statement = f"COPY {relation_name} FROM type_relations"
        conn.execute(statement)
