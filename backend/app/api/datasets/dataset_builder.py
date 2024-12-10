from abc import ABC, abstractmethod

import kuzu
import numpy as np
import pandas as pd
from prefect import get_run_logger
from sqlmodel import Session

from app.api.kuzu.datatypes import NUMERIC_PROPERTY_TYPES, SYMBOLIC_PROPERTY_TYPES
from app.models import (
    Dataset,
    DatasetSchema,
    DatasetSpecifications,
    DatasetStatistics,
    GraphDisplaySpecifications,
    NodeProperty,
    NodeType,
    NumericPropertyInterval,
    NumericPropertyStatistics,
    RelationProperty,
    RelationType,
    SymbolicPropertyStatistics,
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
                    property_type = table_info_result_item[2]
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

        def _fill_up_property_to_statistics(
            property_to_statistics, properties, graph_element_df, variable_name: str
        ):
            for property in properties:
                property_column_name = f"{variable_name}.{property.name}"
                if property.type in NUMERIC_PROPERTY_TYPES:
                    property_to_statistics[property.name] = NumericPropertyStatistics(
                        **graph_element_df[property_column_name]
                        .agg(["min", "max", "mean", "median", "std"])
                        .replace(np.nan, None)
                        .to_dict(),
                        bins=[
                            NumericPropertyInterval(
                                n=n,
                                min_max_counts=[
                                    (interval.left, interval.right, count)
                                    for interval, count in pd.cut(
                                        graph_element_df[property_column_name],
                                        bins=n,
                                        duplicates="drop",
                                    )
                                    .value_counts()
                                    .sort_index()
                                    .items()
                                ],
                            )
                            for n in [10]
                        ],
                        quantiles=[
                            NumericPropertyInterval(
                                n=q,
                                min_max_counts=[
                                    (interval.left, interval.right, count)
                                    for interval, count in pd.qcut(
                                        graph_element_df[property_column_name],
                                        q=q,
                                        duplicates="drop",
                                    )
                                    .value_counts()
                                    .items()
                                ],
                            )
                            for q in [10]
                        ],
                    )
                elif property.type in SYMBOLIC_PROPERTY_TYPES:
                    value_counts = list(
                        graph_element_df[property_column_name]
                        .replace(np.nan, None)
                        .value_counts(dropna=False)
                        .items()
                    )
                    value_counts_max = 10
                    if len(value_counts) > value_counts_max:
                        value_counts = value_counts[:value_counts_max]
                    else:
                        value_counts_max = None
                    property_to_statistics[property.name] = SymbolicPropertyStatistics(
                        value_counts_max=value_counts_max,
                        value_counts=value_counts,
                    )

        logger.info("extract statistics for node properties")
        for node_type in self.dataset.dataset_schema.node_types:
            if node_type.name not in statistics.node_type_to_property_to_statistics:
                statistics.node_type_to_property_to_statistics[node_type.name] = {}
            property_to_statistics = statistics.node_type_to_property_to_statistics[
                node_type.name
            ]
            df = conn.execute(f"MATCH (n:{node_type.name}) RETURN n.*").get_as_df()
            _fill_up_property_to_statistics(
                property_to_statistics, node_type.properties, df, "n"
            )

        logger.info("extract statistics for relation properties")
        for relation_type in self.dataset.dataset_schema.relation_types:
            if (
                relation_type.name
                not in statistics.relation_type_to_property_to_statistics
            ):
                statistics.relation_type_to_property_to_statistics[
                    relation_type.name
                ] = {}
            property_to_statistics = statistics.relation_type_to_property_to_statistics[
                relation_type.name
            ]
            df = conn.execute(
                f"MATCH ()-[r:{relation_type.name}]->() RETURN r.*"
            ).get_as_df()
            _fill_up_property_to_statistics(
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
