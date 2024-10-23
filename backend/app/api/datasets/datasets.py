import logging
from pathlib import Path

import kuzu

from app.models import (
    Dataset,
    DatasetContentPublic,
    NodePublic,
    RelationPublic,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_dataset_from_kuzu(
    dataset: Dataset,
) -> DatasetContentPublic:
    # Initialize database
    db_path: Path = Path(dataset.kuzu_path)
    if not (db_path.exists() and db_path.is_dir()):
        raise RuntimeError("Specified dataset does not exist.")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    logger.info("retrieve all relations")
    result = conn.execute("MATCH ()-[r]->() RETURN *;")
    df = result.get_as_df()
    relations: list[RelationPublic] = []
    for _, row in df.iterrows():
        relations.append(
            RelationPublic(
                source=f'{row["r"]["_src"]["offset"]}_{row["r"]["_src"]["table"]}',
                target=f'{row["r"]["_dst"]["offset"]}_{row["r"]["_dst"]["table"]}',
                type=row["r"]["_label"],
            )
        )

    logger.info("retrieve all nodes")
    result = conn.execute("MATCH (n) RETURN *;")
    df = result.get_as_df()
    nodes: list[NodePublic] = []
    for _, row in df.iterrows():
        nodes.append(
            NodePublic(
                id=f'{row["n"]["_id"]["offset"]}_{row["n"]["_id"]["table"]}',
                type=row["n"]["_label"],
            )
        )

    dataset_content_public = DatasetContentPublic(relations=relations, nodes=nodes)

    return dataset_content_public
