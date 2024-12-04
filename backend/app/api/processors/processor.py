from abc import ABC, abstractmethod

from sqlmodel import Session

from app.models import Dataset, ProcessorSpecifications


class Processor(ABC):
    """
    Runs some processing on a dataset. Results are written as one or more fields on the dataset elements.
    """

    def __init__(self, dataset: Dataset, specifications: ProcessorSpecifications):
        self.dataset = dataset
        self.specifications = specifications

    def check_for_field_conflict(self, session: Session) -> None:
        """
        Raises a exception if an existing field would be overriden by processing results
        """
        for output_properties_pattern in self.specifications.output_properties_patterns:
            for graph_element_types, graph_element_nature in [
                (self.dataset.dataset_schema.node_types, "node"),
                (self.dataset.dataset_schema.relation_types, "relation"),
            ]:
                for graph_element_type in graph_element_types:
                    for property in graph_element_type.properties:
                        assert not output_properties_pattern.matches(
                            graph_element_nature, graph_element_type.name, property.name
                        ), f"Property [{graph_element_nature}].{graph_element_type.name}.{property.name} would be overriden by processing results."

    @abstractmethod
    def run_processing(self, session: Session) -> None:
        """
        Runs the processing.
        """
        pass
