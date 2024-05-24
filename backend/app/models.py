from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


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
    other = "other"


class DglkeDatasetSpecifications(SQLModel):
    initial_dataset: DlgkeAvailableDataset
    splits: list[DatasetSplit] = Field(
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780
        schema_extra={
            "json_schema_extra": {
                "uniqueItems": True,
            }
        }
    )


class StixDatasetSpecifications(SQLModel):
    file_content: str = Field(
        # TODO: use directly json_schema_extra once this is solved: https://github.com/tiangolo/sqlmodel/discussions/780
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


class DatasetBase(SQLModel):
    name: str


class DatasetCreate(DatasetBase):
    name: str
    specifications: DglkeDatasetSpecifications | StixDatasetSpecifications
    sampling: DatasetRatioSampling | DatasetCountSampling | None


class DatasetPublic(DatasetBase):
    id: int
    owner_id: int


class Dataset(DatasetBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    kuzu_path: str
    owner_id: int | None = Field(default=None, foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="datasets")
    # specifications
    specifications_class: str
    specifications_value: str
    # sampling
    sampling_ratio: float | None = Field(gt=0, le=1)
    sampling_count: int | None = Field(gt=0)
