import kuzu
import numpy as np
import pandas as pd
from dglke.dataloader import KGDataset, KGDatasetFB15k, KGDatasetWN18
from prefect import get_run_logger
from slugify import slugify
from sqlmodel import Session

from app.api.datasets.dataset_builder import DatasetBuilder
from app.models import (
    Dataset,
    DatasetSchema,
    DatasetSplit,
    DglkeDatasetSpecifications,
    DlgkeAvailableDataset,
)
from app.utils import setup_kuzu_connection


class DglkeDatasetBuilder(DatasetBuilder):
    def __init__(self, dataset: Dataset, specifications: DglkeDatasetSpecifications):
        super().__init__(dataset, specifications)

    @staticmethod
    def _label_to_class_or_relation(label: str) -> str:
        return slugify(label).replace("-", " ").title().replace(" ", "")

    _UNIQUE_CLASS_NAME = "Node"
    _UNIQUE_RELATION_NAME = "Relation"  # used only when one_relation_type is True
    _RELATION_TYPE_PROPERTY = (
        "_relation_type"  # used only when one_relation_type is True
    )
    _AVAILABLE_DATASET_TO_DGLKE_CLASS: dict[DlgkeAvailableDataset, type[KGDataset]] = {
        DlgkeAvailableDataset.KGDatasetFB15k: KGDatasetFB15k,
        DlgkeAvailableDataset.KGDatasetWN18: KGDatasetWN18,
    }

    @setup_kuzu_connection(create_database=True)
    def instantiate_dataset_in_kuzu(
        self, session: Session, conn: kuzu.Connection
    ) -> DatasetSchema:
        logger = get_run_logger()
        assert isinstance(self.specifications, DglkeDatasetSpecifications)

        dglke_class = self._AVAILABLE_DATASET_TO_DGLKE_CLASS[
            self.specifications.initial_dataset
        ]
        dglke_dataset = dglke_class(path="./dglke_datasets/")

        logger.info("create unique Node class")
        conn.execute(
            f"CREATE NODE TABLE {self._UNIQUE_CLASS_NAME}(id INT64, label STRING, PRIMARY KEY (id))"
        )

        logger.info("create all Node instances")
        nodes = pd.DataFrame(  # noqa: F841
            [(id, label) for label, id in dglke_dataset.entity2id.items()],
            columns=["id", "label"],
        )
        if (
            self.dataset.sampling_count is not None
            or self.dataset.sampling_ratio is not None
        ):
            logger.info("apply sampling on nodes")
            nodes = nodes.sample(
                n=self.dataset.sampling_count,
                frac=self.dataset.sampling_ratio,
            )
        conn.execute(f"COPY {self._UNIQUE_CLASS_NAME} FROM nodes;")

        if self.specifications.one_relation_type:
            logger.info("create relation type")
            conn.execute(
                f"CREATE REL TABLE {self._UNIQUE_RELATION_NAME}(FROM {self._UNIQUE_CLASS_NAME} TO {self._UNIQUE_CLASS_NAME}, {self._RELATION_TYPE_PROPERTY} STRING);"
            )
        else:
            logger.info("create relation types")
            for relation_type in dglke_dataset.relation2id.keys():
                conn.execute(
                    f"CREATE REL TABLE {self._label_to_class_or_relation(relation_type)}(FROM {self._UNIQUE_CLASS_NAME} TO {self._UNIQUE_CLASS_NAME});"
                )

        logger.info("get data from specified splits")
        subjects, relations, objects = (
            np.empty(
                shape=[
                    0,
                ],
                dtype=np.int64,
            ),
        ) * 3
        for split_id, split_content in [
            (DatasetSplit.train, dglke_dataset.train),
            (DatasetSplit.validation, dglke_dataset.valid),
            (DatasetSplit.test, dglke_dataset.test),
        ]:
            if split_id in self.specifications.splits:
                subjects = np.append(subjects, split_content[0])
                relations = np.append(relations, split_content[1])
                objects = np.append(objects, split_content[2])
        if self.dataset.sampling_count or self.dataset.sampling_ratio:
            logger.info("apply sampling on relations")
            # only keep relations linking nodes which have been previously sampled
            to_keep = np.isin(subjects, nodes.id) & np.isin(objects, nodes.id)
            subjects, relations, objects = (
                subjects[to_keep],
                relations[to_keep],
                objects[to_keep],
            )
        logger.info("create relation triples")
        id2relation = {
            id: self._label_to_class_or_relation(relation)
            for relation, id in dglke_dataset.relation2id.items()
        }
        relations_df: pd.DataFrame = pd.DataFrame(
            {"f": subjects, "t": objects, self._RELATION_TYPE_PROPERTY: relations}
        )
        relations_df[self._RELATION_TYPE_PROPERTY] = relations_df[
            self._RELATION_TYPE_PROPERTY
        ].apply(lambda id: id2relation[id])
        if self.specifications.one_relation_type:
            logger.info("create relation triples of type relation")
            statement: str = f"COPY {self._UNIQUE_RELATION_NAME} FROM relations_df"
            conn.execute(statement)
        else:
            for relation_name in dglke_dataset.relation2id.keys():
                logger.info(f"create relation triples of type {relation_name}")
                type_relations_df = relations_df[
                    relations_df[self._RELATION_TYPE_PROPERTY]
                    == self._label_to_class_or_relation(relation_name)
                ]
                if type_relations_df.size > 0:
                    type_relations_df = type_relations_df.drop(
                        self._RELATION_TYPE_PROPERTY, axis=1
                    )
                    statement: str = f"COPY {self._label_to_class_or_relation(relation_name)} FROM type_relations_df"
                    conn.execute(statement)

        logger.info("set dataset schema in database")
        self._set_schema(session)
