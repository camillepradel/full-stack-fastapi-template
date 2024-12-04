import kuzu
import networkx as nx
import pandas as pd
from prefect import get_run_logger
from sqlmodel import Session

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
                pageranks, orient="index", columns=["pagerank"]
            )

            logger.info("save result into graph")
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
                    + f"ON MATCH SET n.{alg_specs.pagerank_property_name} = pagerank\n"
                    + f"RETURN n.{node_type.primary_key.name} AS nodeId, n.{alg_specs.pagerank_property_name} AS pagerank;"
                )

            logger.info("update dataset schema in database")
            for node_type in self.dataset.dataset_schema.node_types:
                node_type.properties.append(
                    NodeProperty(
                        name=alg_specs.pagerank_property_name, type=PROPERTY_TYPE
                    )
                )
            # below line is to force update of dataset in db
            # TODO: this is a hack and we should find a better way
            self.dataset.dataset_schema.node_types = (
                self.dataset.dataset_schema.node_types.copy()
            )
            session.add(self.dataset)
            session.commit()

        # elif isinstance(alg_specs, NetworkXHitsSpecifications):
        #     TODO

        else:
            raise ValueError("Algorithm specifications not supported")
