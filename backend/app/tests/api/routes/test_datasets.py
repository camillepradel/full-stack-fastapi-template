from pathlib import Path

import kuzu
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models import Dataset, DatasetCreate, StixDatasetSpecifications


def _assert_result_count(conn, query, expected_count):
    result = conn.execute(query)
    assert result.get_num_tuples() == expected_count


def test_create_stix_dataset(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    stix_content = (
        Path(__file__).parent.parent.parent / "data" / "threat_actor_profile.json"
    ).read_text()
    dataset_create: DatasetCreate = DatasetCreate(
        name="test_stix_dataset",
        specifications=StixDatasetSpecifications(file_content=stix_content),
        sampling=None,
    )
    response = client.post(
        f"{settings.API_V1_STR}/datasets/",
        headers=superuser_token_headers,
        json=dataset_create.model_dump(),
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == dataset_create.name
    # assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content

    with Session(engine) as session:
        db_dataset = session.get(Dataset, content["id"])
        assert db_dataset
        assert db_dataset.name == content["name"]
        assert db_dataset.owner_id == content["owner_id"]
        kuzu_path: str = db_dataset.kuzu_path

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
