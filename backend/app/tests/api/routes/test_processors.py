import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.core.config import settings
from app.models import (
    ApplyProcessor,
    DatasetContent,
    NetworkXPagerankSpecifications,
    NetworkXProcessorSpecifications,
    NodeType,
)
from app.tests.api.routes.test_datasets import (
    _create_stix_dataset,
    _get_dataset_content,
)


def _apply_networkx_processor_pagerank(
    dataset_id: str,
    pagerank_field_name: str,
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> Response:
    apply_processor: ApplyProcessor = ApplyProcessor(
        dataset_id=dataset_id,
        specifications=NetworkXProcessorSpecifications(
            algorithm_specifications=NetworkXPagerankSpecifications(
                pagerank_property_name=pagerank_field_name,
                directed=False,
            )
        ),
    )
    response = client.post(
        f"{settings.API_V1_STR}/datasets/apply_processor",
        headers=superuser_token_headers,
        json=apply_processor.model_dump(),
    )
    return response


@pytest.mark.parametrize(
    "dataset_name,input_files",
    [
        (
            # dataset_name
            "one json STIX file",
            # input_files
            ["threat_actor_profile.json"],
        ),
    ],
)
def test_networkx_processor_pagerank(
    dataset_name: str,
    input_files: list[str],
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    dataset_name = "test_stix_dataset"
    create_response: Response = _create_stix_dataset(
        dataset_name, input_files, client, superuser_token_headers
    )
    content = create_response.json()
    dataset_id = content["id"]
    pagerank_field_name = "pagerank"
    apply_networkx_processor_response = _apply_networkx_processor_pagerank(
        dataset_id,
        pagerank_field_name,
        client,
        superuser_token_headers,
    )
    assert apply_networkx_processor_response.status_code == 200
    get_content_response: Response = _get_dataset_content(
        dataset_id, client, superuser_token_headers
    )
    assert get_content_response.status_code == 200
    content = get_content_response.json()
    dataset_content: DatasetContent = DatasetContent.model_validate(content)
    print(content)

    # check pagerank values have been processed
    assert len(dataset_content.nodes) == 2
    assert dataset_content.nodes[0].data[pagerank_field_name] == 0.5
    assert dataset_content.nodes[1].data[pagerank_field_name] == 0.5

    # check schema has been updated
    node_types: tuple[NodeType] = dataset_content.metadata_.dataset_schema.node_types
    assert len(node_types) == 2
    assert (
        len(
            [
                prop
                for prop in node_types[0].properties
                if prop.name == pagerank_field_name and prop.type == "DOUBLE"
            ]
        )
        == 1
    )
    assert (
        len(
            [
                prop
                for prop in node_types[1].properties
                if prop.name == pagerank_field_name and prop.type == "DOUBLE"
            ]
        )
        == 1
    )
