from abc import ABC, abstractmethod

import kuzu
from prefect import get_run_logger
from sqlmodel import Session

from app.api.datasets.statistics import fill_up_property_to_statistics
from app.models import (
    Dataset,
    DatasetSchema,
    DatasetSpecifications,
    DatasetStatistics,
    GraphDisplaySpecifications,
    NodeProperty,
    NodeType,
    RelationProperty,
    RelationType,
)
from app.utils import setup_kuzu_connection


class DatasetBuilder(ABC):
    """
    Abstract base class for building datasets.
    Subclasses must implement the abstract methods.
    """

    def __init__(self, dataset: Dataset, specifications: DatasetSpecifications):
        self.dataset = dataset
        self.specifications = specifications

    def get_graph_display_specifications(self) -> GraphDisplaySpecifications:
        """
        Returns a dictionary containing specifications for displaying the dataset in a graph.
        """
        return None

    @setup_kuzu_connection()
    def _get_schema(self, conn: kuzu.Connection) -> DatasetSchema:
        """
        Extract the complete schema from a Kùzu database.
        """
        schema = DatasetSchema()

        # extract node and relations types
        show_tables_query = "CALL show_tables() RETURN *;"
        show_tables_result = conn.execute(show_tables_query)
        while show_tables_result.has_next():
            show_tables_result_item = show_tables_result.get_next()
            type_name = show_tables_result_item[0]
            node_or_rel = show_tables_result_item[1]

            # extract properties
            table_info_query: str = f"CALL TABLE_INFO('{type_name}') RETURN *;"
            table_info_result = conn.execute(table_info_query)
            if node_or_rel == "NODE":
                properties: list[NodeProperty] = []
                while table_info_result.has_next():
                    table_info_result_item = table_info_result.get_next()
                    property_name = table_info_result_item[1]
                    # we use .upper() because type returned by kuzu can be lowercase
                    property_type = table_info_result_item[2].upper()
                    is_primary_key = table_info_result_item[3]
                    properties.append(
                        NodeProperty(
                            name=property_name,
                            type=property_type,
                            is_primary_key=is_primary_key,
                        )
                    )
                schema.node_types.append(
                    NodeType(name=type_name, properties=properties)
                )
            else:
                properties: list[RelationProperty] = []
                while table_info_result.has_next():
                    table_info_result_item = table_info_result.get_next()
                    property_name = table_info_result_item[1]
                    property_type = table_info_result_item[2]
                    properties.append(
                        RelationProperty(name=property_name, type=property_type)
                    )
                schema.relation_types.append(
                    RelationType(name=type_name, properties=properties)
                )

        return schema

    def _set_schema(self, session: Session):
        schema: DatasetSchema = self._get_schema()
        self.dataset.dataset_schema = schema
        session.add(schema)
        session.add(self.dataset)
        session.commit()

    @setup_kuzu_connection()
    def _get_statistics(self, conn: kuzu.Connection) -> DatasetSchema:
        """
        Extract statistics from a Kùzu database.
        """
        logger = get_run_logger()
        statistics = DatasetStatistics()

        logger.info("extract statistics for node properties")
        for node_type in self.dataset.dataset_schema.node_types:
            property_to_statistics = (
                statistics.get_or_create_node_property_to_statistics(node_type.name)
            )
            df = conn.execute(f"MATCH (n:{node_type.name}) RETURN n.*").get_as_df()
            fill_up_property_to_statistics(
                property_to_statistics, node_type.properties, df, "n"
            )

        logger.info("extract statistics for relation properties")
        for relation_type in self.dataset.dataset_schema.relation_types:
            property_to_statistics = (
                statistics.get_or_create_relation_property_to_statistics(
                    relation_type.name
                )
            )
            df = conn.execute(
                f"MATCH ()-[r:{relation_type.name}]->() RETURN r.*"
            ).get_as_df()
            fill_up_property_to_statistics(
                property_to_statistics, relation_type.properties, df, "r"
            )

        return statistics

    def _set_statistics(self, session: Session):
        statistics: DatasetStatistics = self._get_statistics()
        self.dataset.statistics = statistics
        session.add(statistics)
        session.add(self.dataset)
        session.commit()

    @abstractmethod
    def instantiate_dataset_in_kuzu(self, session: Session) -> DatasetSchema:
        """
        Instantiates the dataset in the Kuzu DB and set its schema in PG DB.
        """
        pass
