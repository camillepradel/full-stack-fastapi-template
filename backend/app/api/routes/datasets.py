import inspect
from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter
from sqlmodel import func, select

from app.api.datasets.dglke_datasets import (
    instanciate_dataset_in_kuzu as dglke_instanciate_dataset_in_kuzu,
)
from app.api.datasets.stix_datasets import (
    instanciate_dataset_in_kuzu as stix_instanciate_dataset_in_kuzu,
)
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Dataset,
    DatasetCountSampling,
    DatasetCreate,
    DatasetPublic,
    DatasetRatioSampling,
    DatasetsPublic,
    DglkeDatasetSpecifications,
    StixDatasetSpecifications,
)
from app.utils import get_timestamp_str

router = APIRouter()


@router.get("/", response_model=DatasetsPublic)
def read_datasets(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> DatasetsPublic:
    """
    Retrieve datasets of current user.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Dataset)
        count = session.exec(count_statement).one()
        statement = select(Dataset).offset(skip).limit(limit)
        datasets: Sequence[Dataset] = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Dataset)
            .where(Dataset.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Dataset)
            .where(Dataset.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        datasets: Sequence[Dataset] = session.exec(statement).all()

    return DatasetsPublic(data=datasets, count=count)


@router.post("/", response_model=DatasetPublic)
def create_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_create: DatasetCreate,
) -> Dataset:
    """
    Create a new dataset.

    Args:
        session (SessionDep): The database session.
        current_user (CurrentUser): The current user.
        dataset_create (DatasetCreate): Instructions to create the dataset.

    Returns:
        Dataset: The created dataset.
    """
    # Generate a timestamped name for the dataset
    kuzu_path = f"{get_timestamp_str()}_{dataset_create.name}"

    # Serialize dataset specifications
    specifications_module_name = inspect.getmodule(
        type(dataset_create.specifications)
    ).__name__
    specifications_class_name = type(dataset_create.specifications).__name__
    specifications_value = dataset_create.specifications.model_dump_json()

    # Create and save the dataset info in DB
    dataset = Dataset().model_validate(
        dataset_create,
        update={
            "owner_id": current_user.id,
            "kuzu_path": kuzu_path,
            "specifications_module_name": specifications_module_name,
            "specifications_class_name": specifications_class_name,
            "specifications_value": specifications_value,
            "sampling_ratio": (
                dataset_create.sampling.ratio
                if dataset_create.sampling
                and isinstance(dataset_create.sampling, DatasetRatioSampling)
                else None
            ),
            "sampling_count": (
                dataset_create.sampling.count
                if dataset_create.sampling
                and isinstance(dataset_create.sampling, DatasetCountSampling)
                else None
            ),
        },
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    # Instantiate the dataset in Kuzu
    if isinstance(dataset_create.specifications, DglkeDatasetSpecifications):
        dglke_instanciate_dataset_in_kuzu(dataset, dataset_create.specifications)
    elif isinstance(dataset_create.specifications, StixDatasetSpecifications):
        stix_instanciate_dataset_in_kuzu(dataset, dataset_create.specifications)
    else:
        raise ValueError("Specifications not supported")

    return dataset


@router.get("/create-options/", response_model=dict[str, Any])
def get_create_options() -> dict[str, Any]:
    """
    Get all options to create a new dataset.

    Returns:
        dict[str, Any]: The JSON schema for all options to create a new dataset.
    """
    json_schema: dict[str, Any] = DatasetCreate.model_json_schema()
    return json_schema
