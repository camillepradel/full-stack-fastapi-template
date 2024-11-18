import sys
import uuid
from enum import Enum

from prefect.client.schemas import StateType
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
    file_content: str = Field(
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780 / 833
        schema_extra={
            "json_schema_extra": {
                "format": "data-url",
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
        },
    )
    relations: list[Relation]
    nodes: list[Node]


class WorkflowType(str, Enum):
    build_dataset = "build_dataset"


# Shared properties
class WorkflowBase(SQLModel):
    type: WorkflowType
    description: str
    state: StateType
    # TODO: add timestamp_start, timestamp_end


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
