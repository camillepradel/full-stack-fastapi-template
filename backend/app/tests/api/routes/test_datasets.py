import base64
import operator
from pathlib import Path

import kuzu
import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.models import (
    Dataset,
    DatasetCountSampling,
    DatasetCreate,
    DatasetFilters,
    DatasetSplit,
    DglkeDatasetSpecifications,
    DlgkeAvailableDataset,
    GraphElementFilter,
    RuleGroup,
    StixDatasetSpecifications,
)


def _assert_result_count(conn, query, expected_count, operator=operator.eq):
    result = conn.execute(query)
    assert operator(result.get_num_tuples(), expected_count)


def _create_stix_dataset(
    dataset_name: str,
    input_files: list[str],
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> Response:
    files_content = []
    for input_file in input_files:
        stix_content = (
            Path(__file__).parent.parent.parent / "data" / input_file
        ).read_text()
        files_content.append(
            (
                "data:application/octet-stream;"
                if input_file.endswith(".jsonl")
                else "data:application/json;"
            )
            + f"name={input_file};base64,"
            + base64.b64encode(stix_content.encode("utf-8")).decode("utf-8")
        )
    dataset_create: DatasetCreate = DatasetCreate(
        name=dataset_name,
        specifications=StixDatasetSpecifications(files_content=files_content),
        sampling=None,
    )
    response = client.post(
        f"{settings.API_V1_STR}/datasets/",
        headers=superuser_token_headers,
        json=dataset_create.model_dump(),
    )
    return response


def _create_dglke_dataset(
    dataset_name: str,
    client: TestClient,
    superuser_token_headers: dict[str, str],
    initial_dataset,
    one_relation_type: bool,
    sampling_count: int,
) -> Response:
    dataset_create: DatasetCreate = DatasetCreate(
        name=dataset_name,
        specifications=DglkeDatasetSpecifications(
            initial_dataset=initial_dataset,
            splits=[DatasetSplit.test],
            one_relation_type=one_relation_type,
        ),
        sampling=DatasetCountSampling(count=sampling_count),
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


def _get_dataset_content(
    dataset_id: int,
    filters: DatasetFilters,
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> Response:
    response = client.post(
        f"{settings.API_V1_STR}/datasets/{dataset_id}/content",
        headers=superuser_token_headers,
        json=filters.model_dump(),
    )
    return response


def _create_dataset_common_tests(response, dataset_name):
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

    # TODO: assert that kuzu_path exists
    return kuzu_path


def _threat_actor_profile_tests(result) -> None:
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


@pytest.mark.parametrize(
    "dataset_name,input_files,nodes_count,relations_count,more_tests",
    [
        (
            # dataset_name
            "one json STIX file",
            # input_files
            ["threat_actor_profile.json"],
            # nodes_count
            2,
            # relations_count
            1,
            # more_tests
            _threat_actor_profile_tests,
        ),
        (
            # dataset_name
            "two json STIX files",
            # input_files
            ["threat_actor_profile.json", "defining-campaign-ta-is.json"],
            # nodes_count
            10,
            # relations_count
            19,
            # more_tests
            None,
        ),
        (
            # dataset_name
            "one jsonl file",
            # input_files
            ["threat_actor_profile.jsonl"],
            # nodes_count
            2,
            # relations_count
            1,
            # more_tests
            _threat_actor_profile_tests,
        ),
        (
            # dataset_name
            "one jsonl file + one json STIX file",
            # input_files
            ["threat_actor_profile.jsonl", "defining-campaign-ta-is.json"],
            # nodes_count
            10,
            # relations_count
            19,
            # more_tests
            None,
        ),
    ],
)
def test_create_stix_dataset(
    dataset_name: str,
    input_files: list[str],
    nodes_count: int,
    relations_count: int,
    more_tests,
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    dataset_name = "test_stix_dataset"
    response = _create_stix_dataset(
        dataset_name, input_files, client, superuser_token_headers
    )
    kuzu_path = _create_dataset_common_tests(response, dataset_name)

    # check that the graph is stored in Kuzu
    db = kuzu.Database(kuzu_path)
    conn = kuzu.Connection(db)
    _assert_result_count(conn, "MATCH (n) RETURN n;", nodes_count)
    result = conn.execute("MATCH (n1)-[r]->(n2) RETURN n1, r, n2;")
    assert result.get_num_tuples() == relations_count
    if more_tests:
        more_tests(result)

    # TODO: test the created schema (in this test or somewhere else)
    # TODO: test the created statistics (in this test or somewhere else)


def test_create_dglke_dataset(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    dataset_name = "test_dglke_dataset"
    sampling_count = 500
    response = _create_dglke_dataset(
        dataset_name,
        client,
        superuser_token_headers,
        initial_dataset=DlgkeAvailableDataset.KGDatasetFB15k,
        one_relation_type=True,
        sampling_count=sampling_count,
    )
    kuzu_path = _create_dataset_common_tests(response, dataset_name)

    # check that the graph is stored in Kuzu
    db = kuzu.Database(kuzu_path)
    conn = kuzu.Connection(db)
    _assert_result_count(conn, "MATCH (n) RETURN n;", sampling_count)
    _assert_result_count(conn, "MATCH ()-[r]->() RETURN r;", 1, operator=operator.ge)
    result = conn.execute("MATCH (n) RETURN distinct LABEL(n);")
    assert result.get_num_tuples() == 1
    result_tuple = result.get_next()
    assert len(result_tuple) == 1
    assert result_tuple[0] == "Node"
    result = conn.execute("MATCH ()-[r]->() RETURN distinct LABEL(r);")
    assert result.get_num_tuples() == 1
    result_tuple = result.get_next()
    assert len(result_tuple) == 1
    assert result_tuple[0] == "Relation"

    dataset_name = "test_dglke_dataset_2"
    sampling_count = 5000
    response = _create_dglke_dataset(
        dataset_name,
        client,
        superuser_token_headers,
        initial_dataset=DlgkeAvailableDataset.KGDatasetWN18,
        one_relation_type=False,
        sampling_count=sampling_count,
    )
    kuzu_path = _create_dataset_common_tests(response, dataset_name)

    # check that the graph is stored in Kuzu
    db = kuzu.Database(kuzu_path)
    conn = kuzu.Connection(db)
    _assert_result_count(conn, "MATCH (n) RETURN n;", sampling_count)
    _assert_result_count(conn, "MATCH ()-[r]->() RETURN r;", 1, operator=operator.ge)
    result = conn.execute("MATCH (n) RETURN distinct LABEL(n);")
    assert result.get_num_tuples() == 1
    result_tuple = result.get_next()
    assert len(result_tuple) == 1
    assert result_tuple[0] == "Node"
    result = conn.execute("MATCH ()-[r]->() RETURN distinct LABEL(r);")
    assert 1 < result.get_num_tuples() <= 18


def _assert_count_by_type(graph_elements, type, expected_count) -> None:
    assert (
        len([element for element in graph_elements if element["type"] == type])
        == expected_count
    )


def test_get_dataset_content(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    stix_dataset_name = "test_stix_dataset"
    response = _create_stix_dataset(
        stix_dataset_name,
        ["threat_actor_profile.json", "defining-campaign-ta-is.json"],
        client,
        superuser_token_headers,
    )
    assert response.status_code == 200
    stix_dataset_id = response.json()["id"]

    for (
        filters,
        node_expected_count,
        node_types_expected_counts,
        relation_expected_count,
    ) in [
        (
            DatasetFilters(node_filters=[]),
            10,
            [
                ("ThreatActor", 2),
                ("AttackPattern", 2),
                ("Identity", 3),
                ("IntrusionSet", 1),
                ("Campaign", 2),
            ],
            19,
        ),
        (
            DatasetFilters(
                node_filters=[
                    GraphElementFilter(
                        element_type_name="ThreatActor",
                        select="nothing",
                        filter_value=RuleGroup(combinator="and", rules=[]),
                    )
                ]
            ),
            8,
            [
                ("ThreatActor", 0),
                ("AttackPattern", 2),
                ("Identity", 3),
                ("IntrusionSet", 1),
                ("Campaign", 2),
            ],
            10,
        ),
    ]:
        response = _get_dataset_content(
            stix_dataset_id, filters, client, superuser_token_headers
        )
        assert response.status_code == 200
        content = response.json()

        assert "nodes" in content
        assert "relations" in content

        nodes = content["nodes"]
        assert len(nodes) == node_expected_count
        for node_type, expected_count in node_types_expected_counts:
            _assert_count_by_type(nodes, node_type, expected_count)

        relations = content["relations"]
        assert len(relations) == relation_expected_count
