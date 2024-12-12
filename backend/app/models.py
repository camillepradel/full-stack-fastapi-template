import sys
import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from prefect.client.schemas import StateType
from prefect.client.schemas.objects import Log
from pydantic import TypeAdapter
from sqlalchemy import DateTime, event, func
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


# Shared properties
# TODO replace email str with EmailStr when sqlmodel supports it
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# TODO replace email str with EmailStr when sqlmodel supports it
class UserRegister(SQLModel):
    email: str
    password: str
    full_name: str | None = None


# Properties to receive via API on update, all are optional
# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdate(UserBase):
    email: str | None = None  # type: ignore
    password: str | None = None


# TODO replace email str with EmailStr when sqlmodel supports it
class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: str | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner")
    datasets: list["Dataset"] = Relationship(back_populates="owner")
    workflows: list["Workflow"] = Relationship(back_populates="owner")


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: int


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str
    description: str | None = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = None  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: int
    owner_id: int


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: int | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str


class TimestampedResource(SQLModel):
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": True},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": func.now(), "nullable": True},
    )


class DatasetSplit(str, Enum):
    train = "train"
    validation = "validation"
    test = "test"


class DlgkeAvailableDataset(str, Enum):
    KGDatasetFB15k = "KGDatasetFB15k"
    KGDatasetWN18 = "KGDatasetWN18"


class DatasetSpecifications(SQLModel):
    pass


class DglkeDatasetSpecifications(DatasetSpecifications):
    initial_dataset: DlgkeAvailableDataset
    splits: list[DatasetSplit] = Field(
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780 / 833
        schema_extra={
            "json_schema_extra": {
                "uniqueItems": True,
            }
        }
    )
    one_relation_type: bool = Field(
        True,
        description="If set to `True`, only one relation type with name `relation` "
        "will be created to fit all relations from the dataset, and a property with "
        "name `_relation_type` will be added to each relation to specify the original "
        "relation type. This behaviour is usefull because some datasets have "
        "thousands of relation types and kuzu does not cope well with it. "
        "If set to `False`, each relation type will be created as a separate relation "
        "type.",
    )


class StixDatasetSpecifications(DatasetSpecifications):
    files_content: list[str] = Field(
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780 / 833
        schema_extra={
            "json_schema_extra": {
                "items": {
                    "type": "string",
                    "format": "data-url",
                },
            }
        }
    )


class DatasetRatioSampling(SQLModel):
    ratio: float = Field(gt=0, le=1)


class DatasetCountSampling(SQLModel):
    count: int = Field(gt=0)


class GraphDisplaySpecifications(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # node display:
    # which field to use when displaying node label
    node_label_field_name: str | None = None
    # which icon to use when displaying a node, according to its class
    node_icons: dict[str, str] | None = Field(sa_column=Column(JSON), default=None)


class DatasetBase(SQLModel):
    name: str


class DatasetCreate(DatasetBase):
    specifications: DglkeDatasetSpecifications | StixDatasetSpecifications
    sampling: DatasetRatioSampling | DatasetCountSampling | None = None


class GraphElementProperty(SQLModel):
    name: str
    type: str  # TODO: use enum once it is defined (c.f. ongoing work in api/kuzu/datatypes.py)


class RelationProperty(GraphElementProperty):
    pass


class NodeProperty(GraphElementProperty):
    is_primary_key: bool = False


class GraphElementType(SQLModel):
    name: str


class NodeType(GraphElementType):
    properties: Sequence[NodeProperty]

    @property
    def primary_key(self) -> NodeProperty:
        return next(prop for prop in self.properties if prop.is_primary_key)


class RelationType(GraphElementType):
    properties: Sequence[RelationProperty]


class DatasetSchemaBase(TimestampedResource):
    pass


class DatasetSchema(DatasetSchemaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_types: list[NodeType] = Field(default_factory=list, sa_column=Column(JSON))
    relation_types: list[RelationType] = Field(
        default_factory=list, sa_column=Column(JSON)
    )


class DatasetSchemaPublic(DatasetSchemaBase):
    node_types: list[NodeType]
    relation_types: list[RelationType]


@event.listens_for(DatasetSchema, "before_insert")
@event.listens_for(DatasetSchema, "before_update")
def dataset_schema_dump(
    mapper,  # noqa: ARG001
    connection,  # noqa: ARG001
    target,
) -> DatasetSchema:
    dataset_schema = target
    dataset_schema.node_types = TypeAdapter(list[NodeType]).dump_python(
        dataset_schema.node_types
    )
    dataset_schema.relation_types = TypeAdapter(list[RelationType]).dump_python(
        dataset_schema.relation_types
    )
    return dataset_schema


@event.listens_for(DatasetSchema, "load")
def dataset_schema_validate(
    dataset_schema,
    context,  # noqa: ARG001
) -> DatasetSchema:
    dataset_schema.node_types = TypeAdapter(list[NodeType]).validate_python(
        dataset_schema.node_types
    )
    dataset_schema.relation_types = TypeAdapter(list[RelationType]).validate_python(
        dataset_schema.relation_types
    )
    return dataset_schema


class PropertyStatistics(SQLModel):
    pass


_T = TypeVar("_T")


class SymbolicPropertyStatistics(PropertyStatistics, Generic[_T]):
    value_counts_max: int | None = Field(
        ...,
        description="Maximum number of items which have been saved in value_counts; if None, value_counts is untouched.",
    )
    value_counts: list[tuple[_T, int]] = Field(
        ...,
        description="The list of existing values with their count, sorted in descending order and optinally truncated to `value_counts_max`.",
    )


class NumericPropertyInterval(PropertyStatistics, Generic[_T]):
    n: int = Field(..., description="Number of cuts used to split values span.")
    min_max_counts: list[tuple[_T, _T, int]] = Field(
        ...,
        description="The list of cuts, whether quantiles or bins, expressed with their min value, max value and number of values they contain.",
    )


class NumericPropertyStatistics(SQLModel, Generic[_T]):
    min: _T
    max: _T
    mean: _T
    median: _T
    std: _T
    quantiles: list[NumericPropertyInterval]
    bins: list[NumericPropertyInterval]


class DatasetStatisticsBase(TimestampedResource):
    pass


class DatasetStatistics(DatasetStatisticsBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_type_to_property_to_statistics: dict[
        str, dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None]
    ] = Field(default_factory=dict, sa_column=Column(JSON))
    relation_type_to_property_to_statistics: dict[
        str, dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None]
    ] = Field(default_factory=dict, sa_column=Column(JSON))
    # TODO: add statistics for node and relation types (with at least their counts)


class DatasetStatisticsPublic(DatasetStatisticsBase):
    node_type_to_property_to_statistics: dict[
        str, dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None]
    ]
    relation_type_to_property_to_statistics: dict[
        str, dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None]
    ]


@event.listens_for(DatasetStatistics, "before_insert")
@event.listens_for(DatasetStatistics, "before_update")
def dataset_statistics_dump(
    mapper,  # noqa: ARG001
    connection,  # noqa: ARG001
    target,
) -> DatasetStatistics:
    dataset_statistics = target
    dataset_statistics.node_type_to_property_to_statistics = TypeAdapter(
        dict[
            str,
            dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None],
        ]
    ).dump_python(dataset_statistics.node_type_to_property_to_statistics)
    dataset_statistics.relation_type_to_property_to_statistics = TypeAdapter(
        dict[
            str,
            dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None],
        ]
    ).dump_python(dataset_statistics.relation_type_to_property_to_statistics)
    return dataset_statistics


@event.listens_for(DatasetStatistics, "load")
def dataset_statistics_validate(
    dataset_statistics,
    context,  # noqa: ARG001
) -> DatasetStatistics:
    dataset_statistics.node_type_to_property_to_statistics = TypeAdapter(
        dict[
            str,
            dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None],
        ]
    ).validate_python(dataset_statistics.node_type_to_property_to_statistics)
    dataset_statistics.relation_type_to_property_to_statistics = TypeAdapter(
        dict[
            str,
            dict[str, SymbolicPropertyStatistics | NumericPropertyStatistics | None],
        ]
    ).validate_python(dataset_statistics.relation_type_to_property_to_statistics)
    return dataset_statistics


class Dataset(DatasetBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    kuzu_path: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="datasets")
    # specifications
    specifications_module_name: str
    specifications_class_name: str
    specifications_value: str
    # sampling
    sampling_ratio: float | None = Field(gt=0, le=1)
    sampling_count: int | None = Field(gt=0)

    dataset_schema_id: int | None = Field(
        default=None, foreign_key="datasetschema.id", nullable=True
    )
    dataset_schema: DatasetSchema | None = Relationship()

    statistics_id: int | None = Field(
        default=None, foreign_key="datasetstatistics.id", nullable=True
    )
    statistics: DatasetStatistics | None = Relationship()

    graph_display_specifications_id: int | None = Field(
        default=None, foreign_key="graphdisplayspecifications.id"
    )
    graph_display_specifications: GraphDisplaySpecifications | None = Relationship()

    workflows: list["Workflow"] = Relationship(back_populates="related_dataset")

    def _get_specifications(self):
        # TODO: remove this function if never used
        specifications_class = getattr(
            sys.modules[self.specifications_module_name], self.specifications_class_name
        )
        specifications = specifications_class.model_validate_json(
            self.specifications_value
        )
        return specifications

    def _get_sampling(self) -> DatasetRatioSampling | DatasetCountSampling | None:
        # TODO: remove this function if never used
        sampling = (
            DatasetRatioSampling(ratio=self.sampling_ratio)
            if self.sampling_ratio
            else DatasetCountSampling(count=self.sampling_count)
            if self.sampling_count
            else None
        )
        return sampling


# Properties to return via API, id is always required
class DatasetPublic(DatasetBase):
    id: int
    owner_id: int
    dataset_schema: DatasetSchemaPublic | None
    statistics: DatasetStatistics | None
    graph_display_specifications: GraphDisplaySpecifications | None
    workflows: list["WorkflowPublic"]


class DatasetsPublic(SQLModel):
    data: list[DatasetPublic]
    count: int


class Relation(SQLModel):
    source: str
    target: str
    type: str
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Node(SQLModel):
    id: str
    type: str
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))


class DatasetContent(SQLModel):
    # `metadata` field is already used in SQLModel, so we use metadata_ here and rename the column and json field
    metadata_: DatasetPublic = Field(
        sa_column=Column("metadata"),
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780 / 833
        schema_extra={
            "validation_alias": "metadata",
            "serialization_alias": "metadata",
        },
    )
    relations: list[Relation]
    nodes: list[Node]


class FieldPattern(SQLModel):
    """
    Pattern to refer to a field or a set of fields in a dataset schema.
    """

    graph_element_nature: str  # "node", "relation" or "*"
    graph_element_type_name: str
    property_name: str

    def matches(
        self, graph_element_nature, graph_element_type_name, property_name
    ) -> bool:
        return (
            (
                self.graph_element_nature == "*"
                or self.graph_element_nature == graph_element_nature
            )
            and (
                self.graph_element_type_name == "*"
                or self.graph_element_type_name == graph_element_type_name
            )
            and (self.property_name == "*" or self.property_name == property_name)
        )


class ProcessorSpecifications(SQLModel, ABC):
    @property
    @abstractmethod
    def output_properties_patterns(self) -> list[FieldPattern]:
        """
        List of fields that will be added to the dataset elements.
        """
        pass


class NetworXkAlgorithmSpecifications(SQLModel, ABC):
    @property
    @abstractmethod
    def output_properties(self) -> list[FieldPattern]:
        """
        List of fields that will be added to the dataset elements.
        """
        pass


class NetworkXPagerankSpecifications(NetworXkAlgorithmSpecifications):
    """Specifications on how to run NetworkX PageRank algorithm on the graph and save result (i.e. pagerank values)"""

    pagerank_property_name: str = Field(
        ..., description="The field to save pagerank in."
    )
    directed: bool = Field(
        ...,
        description="Whether or not graph should be considered as directed while running the algorithm.",
    )
    alpha: float = Field(0.85, description="Damping parameter for PageRank.")
    # TODO: add other parameters (https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html#networkx.algorithms.link_analysis.pagerank_alg.pagerank)

    @property
    def output_properties(self) -> list[FieldPattern]:
        return [
            FieldPattern(
                graph_element_nature="node",
                graph_element_type_name="*",
                property_name=self.pagerank_property_name,
            ),
        ]


class NetworkXHitsSpecifications(NetworXkAlgorithmSpecifications):
    """Specifications on how to run NetworkX Hits algorithm on the graph and save result (i.e. authority and hub values)"""

    authority_property_name: str = Field(
        ..., description="The field to save authority in."
    )
    hub_property_name: str = Field(..., description="The field to save hub in.")
    max_iter: int = Field(
        100, description="Maximum number of iterations in power method."
    )
    tol: float = Field(
        1e-08,
        description="Error tolerance used to check convergence in power method iteration.",
    )
    normalized: bool = Field(
        True, description="Normalize results by the sum of all of the values."
    )

    @property
    def output_properties(self) -> list[FieldPattern]:
        return [
            FieldPattern(
                graph_element_nature="node",
                graph_element_type_name="*",
                property_name=self.authority_property_name,
            ),
            FieldPattern(
                graph_element_nature="node",
                graph_element_type_name="*",
                property_name=self.hub_property_name,
            ),
        ]


class NetworkXProcessorSpecifications(ProcessorSpecifications):
    algorithm_specifications: NetworkXPagerankSpecifications | NetworkXHitsSpecifications

    @property
    def output_properties_patterns(self) -> list[FieldPattern]:
        return self.algorithm_specifications.output_properties


class ApplyProcessor(SQLModel):
    dataset_id: int
    specifications: NetworkXProcessorSpecifications  # | ...


class WorkflowType(str, Enum):
    build_dataset = "build_dataset"
    run_processor = "run_processor"


# Shared properties
class WorkflowBase(TimestampedResource):
    type: WorkflowType
    description: str
    state: StateType
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when the workflow started (can be different from `created_at`).",
        sa_type=DateTime(timezone=True),
    )
    ended_at: datetime | None = Field(
        default=None,
        description="Timestamp when the workflow ended.",
        sa_type=DateTime(timezone=True),
    )


# Database model, database table inferred from class name
class Workflow(WorkflowBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="workflows")
    related_dataset_id: int | None = Field(
        default=None, foreign_key="dataset.id", nullable=False
    )
    related_dataset: Dataset | None = Relationship(back_populates="workflows")
    prefect_flow_run_id: uuid.UUID
    is_remote: bool


# Properties to return via API, id is always required
class WorkflowPublic(WorkflowBase):
    id: int
    owner_id: int
    related_dataset_id: int | None


class WorkflowsPublic(SQLModel):
    data: list[WorkflowPublic]
    count: int


class WorkflowContent(SQLModel):
    # `metadata` field is already used in SQLModel, so we use metadata_ here and rename the column and json field
    metadata_: WorkflowPublic = Field(
        sa_column=Column("metadata"),
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780 / 833
        schema_extra={
            "validation_alias": "metadata",
            "serialization_alias": "metadata",
        },
    )
    logs: list[Log]
