from sqlmodel import Session

from app.api.datasets.dglke_dataset_builder import DglkeDatasetBuilder
from app.api.datasets.stix_dataset_builder import StixDatasetBuilder
from app.core.db import engine
from app.models import (
    Dataset,
    DatasetCreate,
    DglkeDatasetSpecifications,
    StixDatasetSpecifications,
    WorkflowType,
)
from app.monitored_flow import monitored_flow


@monitored_flow(
    workflow_type=WorkflowType.build_dataset,
    description="Build dataset",
    related_object_id_arg_name="dataset_id",
)
def build_dataset(
    dataset_id: int,
    dataset_create: DatasetCreate,
):
    with Session(engine) as session:
        dataset: Dataset | None = session.get_one(Dataset, dataset_id)

        # Instantiate DatasetBuilder according to the specifications type
        if isinstance(dataset_create.specifications, StixDatasetSpecifications):
            dataset_builder = StixDatasetBuilder(dataset, dataset_create.specifications)
        elif isinstance(dataset_create.specifications, DglkeDatasetSpecifications):
            dataset_builder = DglkeDatasetBuilder(
                dataset, dataset_create.specifications
            )
        else:
            raise ValueError("Specifications not supported")

        # set graph display specifications adapted to the dataset type
        dataset.graph_display_specifications = (
            dataset_builder.get_graph_display_specifications()
        )
        session.add(dataset)
        session.commit()

        dataset_builder.instantiate_dataset_in_kuzu(session=session)
