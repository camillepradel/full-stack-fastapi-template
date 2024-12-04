from sqlmodel import Session

from app.api.processors.networkx_processor import NetworkXProcessor
from app.core.db import engine
from app.models import (
    ApplyProcessor,
    Dataset,
    NetworkXProcessorSpecifications,
    WorkflowType,
)
from app.monitored_flow import monitored_flow


@monitored_flow(
    workflow_type=WorkflowType.run_processor,
    description="Run processor",
    related_object_id_arg_name="dataset_id",
)
def run_processor(
    dataset_id: int,
    apply_processor: ApplyProcessor,
):
    with Session(engine) as session:
        dataset: Dataset | None = session.get_one(Dataset, dataset_id)

        # Instantiate Processor according to the specifications type
        if isinstance(apply_processor.specifications, NetworkXProcessorSpecifications):
            processor = NetworkXProcessor(dataset, apply_processor.specifications)
        else:
            raise ValueError("Specifications not supported")

        processor.check_for_field_conflict(session=session)
        processor.run_processing(session=session)
