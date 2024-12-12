import kuzu
import networkx as nx
import pandas as pd
from prefect import get_run_logger
from sqlmodel import Session

from app.api.datasets.statistics import fill_up_property_to_statistics
from app.api.kuzu.datatypes import KUZU_TO_PYTHON_TYPES
from app.api.processors.processor import Processor
from app.models import (
    DatasetPublic,
    NetworkXPagerankSpecifications,
    NetworkXProcessorSpecifications,
    NodeProperty,
)
from app.utils import setup_kuzu_connection


class NetworkXProcessor(Processor):
    def __init__(
        self, dataset: DatasetPublic, specifications: NetworkXProcessorSpecifications
    ):
        super().__init__(dataset, specifications)

    @setup_kuzu_connection()
    def run_processing(self, session: Session, conn: kuzu.Connection):
        logger = get_run_logger()
        PROPERTY_TYPE = "DOUBLE"

        assert isinstance(self.specifications, NetworkXProcessorSpecifications)
        alg_specs = self.specifications.algorithm_specifications

        if isinstance(alg_specs, NetworkXPagerankSpecifications):
            logger.info("load graph in memory")
            res = conn.execute("MATCH (s)-[r]->(o) RETURN s, r, o")
            G = res.get_as_networkx(directed=alg_specs.directed)

            logger.info("run pagerank")
            pageranks = nx.pagerank(G, alpha=alg_specs.alpha)
            pagerank_df = pd.DataFrame.from_dict(
                pageranks, orient="index", columns=[alg_specs.pagerank_property_name]
            )

            logger.info(
                "save result into graph and update dataset schema and statistics in database"
            )
            for node_type in self.dataset.dataset_schema.node_types:
                node_type_df = pagerank_df[
                    pagerank_df.index.str.startswith(f"{node_type.name}_")
                ]
                node_type_df.index = node_type_df.index.str.replace(
                    f"{node_type.name}_", ""
                ).astype(KUZU_TO_PYTHON_TYPES[node_type.primary_key.type])
                node_type_df = node_type_df.reset_index(names=["id"])
                try:
                    # Alter original node table schemas to add pageranks
                    conn.execute(
                        f"ALTER TABLE {node_type.name} ADD {alg_specs.pagerank_property_name} {PROPERTY_TYPE} DEFAULT 0.0;"
                    )
                except RuntimeError:
                    # If the column already exists, do nothing
                    pass
                # Copy pagerank values to nodes
                conn.execute(
                    "LOAD FROM node_type_df\n"
                    + "MERGE (n:"
                    + node_type.name
                    + "{"
                    + node_type.primary_key.name
                    + ": id})\n"
                    + f"ON MATCH SET n.{alg_specs.pagerank_property_name} = {alg_specs.pagerank_property_name}\n"
                    + f"RETURN n.{node_type.primary_key.name} AS nodeId, n.{alg_specs.pagerank_property_name} AS pagerank;"
                )

                # schema
                node_property = NodeProperty(
                    name=alg_specs.pagerank_property_name, type=PROPERTY_TYPE
                )
                node_type.properties.append(node_property)

                # statistics
                property_to_statistics = (
                    self.dataset.statistics.get_or_create_node_property_to_statistics(
                        node_type.name
                    )
                )
                fill_up_property_to_statistics(
                    property_to_statistics, [node_property], node_type_df
                )

            # below line is to force update of dataset, schema and statistics in db
            # TODO: this is a hack and we should find a better way
            self.dataset.dataset_schema.node_types = (
                self.dataset.dataset_schema.node_types.copy()
            )
            self.dataset.statistics.node_type_to_property_to_statistics = (
                self.dataset.statistics.node_type_to_property_to_statistics.copy()
            )
            session.add(self.dataset)
            session.commit()

        # elif isinstance(alg_specs, NetworkXHitsSpecifications):
        #     TODO

        else:
            raise ValueError("Algorithm specifications not supported")
