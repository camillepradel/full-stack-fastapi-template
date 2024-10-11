import base64
from pathlib import Path

import kuzu
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models import Dataset, DatasetCreate, StixDatasetSpecifications


def _assert_result_count(conn, query, expected_count):
    result = conn.execute(query)
    assert result.get_num_tuples() == expected_count


def _create_stix_dataset(
    dataset_name: str, client: TestClient, superuser_token_headers: dict[str, str]
) -> Response:
    stix_content = (
        Path(__file__).parent.parent.parent / "data" / "threat_actor_profile.json"
    ).read_text()
    file_content = (
        "data:application/json;name=threat_actor_profile.json;base64,"
        + base64.b64encode(stix_content.encode("utf-8")).decode("utf-8")
    )
    dataset_create: DatasetCreate = DatasetCreate(
        name=dataset_name,
        specifications=StixDatasetSpecifications(file_content=file_content),
        sampling=None,
    )
    response = client.post(
        f"{settings.API_V1_STR}/datasets/",
        headers=superuser_token_headers,
        json=dataset_create.model_dump(),
    )
    return response


def _get_datasets(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> Response:
    response = client.get(
        f"{settings.API_V1_STR}/datasets/",
        headers=superuser_token_headers,
    )
    return response


def test_create_stix_dataset(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dataset_name = "test_stix_dataset"
    response = _create_stix_dataset(dataset_name, client, superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == dataset_name
    assert "id" in content
    assert "owner_id" in content

    # check that the dataset is stored in the database
    with Session(engine) as session:
        db_dataset = session.get(Dataset, content["id"])
        assert db_dataset
        assert db_dataset.name == content["name"]
        assert db_dataset.owner_id == content["owner_id"]
        kuzu_path: str = db_dataset.kuzu_path

    # check that the graph is stored in Kuzu
    db = kuzu.Database(kuzu_path)
    conn = kuzu.Connection(db)
    _assert_result_count(conn, "MATCH (n) RETURN n;", 2)
    result = conn.execute("MATCH (n1)-[r]->(n2) RETURN n1, r, n2;")
    assert result.get_num_tuples() == 1
    result_tuple = result.get_next()
    assert len(result_tuple) == 3
    assert result_tuple[0]["_label"] == "ThreatActor"
    assert result_tuple[0]["name"] == "Disco Team Threat Actor Group"
    assert result_tuple[0]["id"] == "threat-actor--dfaa8d77-07e2-4e28-b2c8-92e9f7b04428"
    assert result_tuple[2]["_label"] == "Identity"
    assert result_tuple[2]["name"] == "Disco Team"
    assert result_tuple[2]["id"] == "identity--733c5838-34d9-4fbf-949c-62aba761184c"
    assert result_tuple[1]["relationship_type"] == "attributed-to"
    assert result_tuple[1]["id"] == "relationship--a2e3efb5-351d-4d46-97a0-6897ee7c77a0"
    assert result.has_next() is False


def test_get_datasets(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    stix_dataset_name = "test_stix_dataset"
    response = _create_stix_dataset(stix_dataset_name, client, superuser_token_headers)
    assert response.status_code == 200
    stix_dataset_id = response.json()["id"]

    # TODO: create at least an other dataset (not a STIX one)

    response = _get_datasets(client, superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1

    # check that the dataset is in the returned datasets
    stix_dataset_content = next(
        (d for d in content["data"] if d["id"] == stix_dataset_id), None
    )
    assert stix_dataset_content
    assert stix_dataset_content["name"] == stix_dataset_name
    assert "owner_id" in stix_dataset_content
