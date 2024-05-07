import math
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

import kuzu
import pandas as pd
from dglke.dataloader import KGDatasetFB15k
from slugify import slugify
from tqdm import tqdm

_T = TypeVar("_T")


def batch(iterable: list[_T], n: int = 1) -> Iterable[list[_T]]:
    iterable_length = len(iterable)
    for ndx in range(0, iterable_length, n):
        yield iterable[ndx : min(ndx + n, iterable_length)]


def label_to_class_or_relation(label: str):
    return slugify(label).replace("-", " ").title().replace(" ", "")


def main() -> None:
    # Initialize database
    db_path: Path = Path(__file__).parent / "demo_db"
    if db_path.exists() and db_path.is_dir():
        shutil.rmtree(db_path)
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    dataset = KGDatasetFB15k(path="./dglke_datasets/")
    print(dataset)

    print("create unique Node class")
    unique_class_name = "Node"
    conn.execute(
        f"CREATE NODE TABLE {unique_class_name}(id INT, label STRING, PRIMARY KEY (id))"
    )

    print("create all Node instances")
    nodes = pd.DataFrame(  # noqa: F841
        list(dataset.entity2id.items()),
        columns=["label", "id"],
    )
    conn.execute(
        "LOAD FROM nodes CREATE (n:" + unique_class_name + " {id: id, label: label});"
    )

    for relation_type in tqdm(
        dataset.relation2id.keys(), desc="create relations types"
    ):
        conn.execute(
            f"CREATE REL TABLE {label_to_class_or_relation(relation_type)}(FROM {unique_class_name} TO {unique_class_name});"
        )

    id2relation = {
        id: label_to_class_or_relation(relation)
        for relation, id in dataset.relation2id.items()
    }
    subjects = dataset.train[0]
    relations = dataset.train[1]
    objects = dataset.train[2]
    batch_size = 50
    for i_triple_range in tqdm(
        batch(range(dataset.train[0].shape[0]), n=batch_size),
        desc="create relation triples",
        total=math.ceil(dataset.train[0].shape[0] / batch_size),
    ):
        entity_ids = set(
            [int(subjects[i_triple]) for i_triple in i_triple_range]
            + [int(objects[i_triple]) for i_triple in i_triple_range]
        )
        # subject_id = subjects[i_triple]
        # relation_id = dataset.train[1][i_triple]
        # object_id = objects
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


if __name__ == "__main__":
    main()
