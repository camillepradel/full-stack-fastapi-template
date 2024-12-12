from collections.abc import Sequence

import numpy as np
import pandas as pd

from app.api.kuzu.datatypes import NUMERIC_PROPERTY_TYPES, SYMBOLIC_PROPERTY_TYPES
from app.models import (
    NodeProperty,
    NumericPropertyInterval,
    NumericPropertyStatistics,
    SymbolicPropertyStatistics,
)


def fill_up_property_to_statistics(
    property_to_statistics: dict[
        str, SymbolicPropertyStatistics | NumericPropertyStatistics | None
    ],
    properties: Sequence[NodeProperty],
    graph_element_df: pd.DataFrame,
    variable_name: str | None = None,
):
    for property in properties:
        property_column_name = (
            f"{variable_name}.{property.name}" if variable_name else property.name
        )
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
