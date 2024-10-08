import logging
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

import kuzu
import numpy as np
import pandas as pd
from dglke.dataloader import KGDataset, KGDatasetFB15k
from slugify import slugify

from app.models import (
    Dataset,
    DglkeDatasetSpecifications,
    DlgkeAvailableDataset,
)

_T = TypeVar("_T")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO: merge with other batch() functions
def batch(iterable: list[_T], n: int = 1) -> Iterable[list[_T]]:
    iterable_length = len(iterable)
    for ndx in range(0, iterable_length, n):
        yield iterable[ndx : min(ndx + n, iterable_length)]


def label_to_class_or_relation(label: str) -> str:
    return slugify(label).replace("-", " ").title().replace(" ", "")


AVAILABLE_DATASET_TO_DGLKE_CLASS: dict[DlgkeAvailableDataset, type[KGDataset]] = {
    DlgkeAvailableDataset.KGDatasetFB15k: KGDatasetFB15k,
}


def instanciate_dataset_in_kuzu(
    dataset: Dataset, specifications: DglkeDatasetSpecifications
):
    # TODO: move below setup lines to a common decorator @setup_kuzu_connection and use
    #       it in all instanciate_dataset_in_kuzu() functions

    assert isinstance(specifications, DglkeDatasetSpecifications)
    # Initialize database
    db_path: Path = Path(dataset.kuzu_path)
    if db_path.exists() and db_path.is_dir():
        raise RuntimeError("Path specified for DB already exists. Abort DB creation.")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    dglke_class = AVAILABLE_DATASET_TO_DGLKE_CLASS[specifications.initial_dataset]
    dglke_dataset = dglke_class(path="./dglke_datasets/")

    logger.info("create unique Node class")
    unique_class_name = "Node"
    conn.execute(
        f"CREATE NODE TABLE {unique_class_name}(id INT, label STRING, PRIMARY KEY (id))"
    )

    logger.info("create all Node instances")
    nodes = pd.DataFrame(  # noqa: F841
        list(dglke_dataset.entity2id.items()),
        columns=["label", "id"],
    )
    if dataset.sampling_count is not None or dataset.sampling_ratio is not None:
        nodes = nodes.sample(
            n=dataset.sampling_count,
            frac=dataset.sampling_ratio,
        )
    conn.execute(
        "LOAD FROM nodes CREATE (n:" + unique_class_name + " {id: id, label: label});"
    )

    logger.info("create relation types")
    for relation_type in dglke_dataset.relation2id.keys():
        conn.execute(
            f"CREATE REL TABLE {label_to_class_or_relation(relation_type)}(FROM {unique_class_name} TO {unique_class_name});"
        )

    logger.info("create relation triples")
    id2relation = {
        id: label_to_class_or_relation(relation)
        for relation, id in dglke_dataset.relation2id.items()
    }
    dataset_split = dglke_dataset.train
    subjects = dataset_split[0]
    relations = dataset_split[1]
    objects = dataset_split[2]
    if dataset.sampling_count or dataset.sampling_ratio:
        to_keep = np.isin(subjects, nodes.id) | np.isin(objects, nodes.id)
        subjects, relations, objects = (
            subjects[to_keep],
            relations[to_keep],
            objects[to_keep],
        )
    batch_size = 50
    for i_triple_range in batch(range(subjects.size), n=batch_size):
        entity_ids = set(
            [int(subjects[i_triple]) for i_triple in i_triple_range]
            + [int(objects[i_triple]) for i_triple in i_triple_range]
        )
        match = "MATCH " + ", ".join(
            [
                "(n_"
                + str(entity_id)
                + ":"
                + unique_class_name
                + " {id:"
                + str(entity_id)
                + "})"
                for entity_id in entity_ids
            ]
        )
        create = "CREATE " + ", ".join(
            [
                f"(n_{subjects[i_triple]})-[:{id2relation[relations[i_triple]]}]->(n_{objects[i_triple]})"
                for i_triple in i_triple_range
            ]
        )
        conn.execute(f"{match}\n{create};")
