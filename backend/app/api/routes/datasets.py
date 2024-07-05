from datetime import datetime
from typing import Any

from fastapi import APIRouter

from app.api.datasets.dglke_datasets import (
    instanciate_dataset_in_kuzu as dglke_instanciate_dataset_in_kuzu,
)
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Dataset,
    DatasetCountSampling,
    DatasetCreate,
    DatasetRatioSampling,
    DglkeDatasetSpecifications,
)

router = APIRouter()


def get_timestamp_str() -> str:
    return str(datetime.now()).replace(" ", "_")


@router.post("/", response_model=Dataset)
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
    specifications_class = str(type(dataset_create.specifications))
    specifications_value = dataset_create.specifications.model_dump_json()

    # Create and save the dataset info in DB
    dataset = Dataset().model_validate(
        dataset_create,
        update={
            "owner_id": current_user.id,
            "kuzu_path": kuzu_path,
            "specifications_class": specifications_class,
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

    # Instantiate the dataset in Kuzu if it's a DGLKE dataset
    if isinstance(dataset_create.specifications, DglkeDatasetSpecifications):
        dglke_instanciate_dataset_in_kuzu(dataset, dataset_create.specifications)
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
