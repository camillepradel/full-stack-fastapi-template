import inspect
from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import func, select

from app.api.datasets.build_dataset import build_dataset
from app.api.datasets.datasets import read_dataset_from_kuzu
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Dataset,
    DatasetContent,
    DatasetCountSampling,
    DatasetCreate,
    DatasetPublic,
    DatasetRatioSampling,
    DatasetsPublic,
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


@router.get("/content/{id}", response_model=DatasetContent)
def read_dataset_content(
    session: SessionDep, current_user: CurrentUser, id: int
) -> DatasetContent:
    """
    Get dataset content (nodes and relations) by ID.
    """
    dataset: Dataset | None = session.get(Dataset, id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not current_user.is_superuser and (dataset.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    dataset_content: DatasetContent = read_dataset_from_kuzu(dataset)

    return dataset_content


@router.post("/", response_model=DatasetPublic)
def create_dataset(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    dataset_create: DatasetCreate,
    background_tasks: BackgroundTasks,
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
    kuzu_path = f"kuzu_data/{get_timestamp_str()}_{dataset_create.name}"

    # Serialize dataset specifications
    specifications_module_name = inspect.getmodule(
        type(dataset_create.specifications)
    ).__name__
    specifications_class_name = type(dataset_create.specifications).__name__
    specifications_value = dataset_create.specifications.model_dump_json()

    # Create and save the dataset into in DB
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

    # build dataset in background
    background_tasks.add_task(
        build_dataset,
        dataset=dataset,
        dataset_create=dataset_create,
        session=session,
        current_user_id=current_user.id,
    )

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
