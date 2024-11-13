from abc import ABC, abstractmethod

from app.models import Dataset, DatasetSpecifications, GraphDisplaySpecifications


class DatasetBuilder(ABC):
    """
    Abstract base class for building datasets.
    Subclasses must implement the abstract methods.
    """

    def __init__(self, dataset: Dataset, specifications: DatasetSpecifications):
        self.dataset = dataset
        self.specifications = specifications

    def get_graph_display_specifications(self) -> GraphDisplaySpecifications:
        """
        Returns a dictionary containing specifications for displaying the dataset in a graph.
        """
        return None

    @abstractmethod
    def instantiate_dataset_in_kuzu(
        self, dataset: Dataset, specifications: DatasetSpecifications
    ) -> None:
        """
        Instantiates the dataset in the Kuzu DB.
        """
        pass
