from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from search.app import app

INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "search" / "index.json"


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_persisted_index():
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()
    yield
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()


def _extract_ids(response_json):
    return [item["id"] for item in response_json["data"]]


def test_keyword_search_returns_matching_question(client):
    response = client.post("/search", json={"query": "embolism"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert _extract_ids(payload) == ["q_1a2b3c4d"]


def test_fuzzy_keyword_search_returns_matching_question(client):
    response = client.post("/search", json={"query": "embolsm"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert _extract_ids(payload) == ["q_1a2b3c4d"]


def test_tag_only_search_filters_results(client):
    response = client.post("/search", json={"tags": ["infection"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert _extract_ids(payload) == ["q_5e6f7a8b"]


def test_combined_query_and_tag_search(client):
    response = client.post("/search", json={"query": "presents", "tags": ["high-yield"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert _extract_ids(payload) == ["q_1a2b3c4d"]


def test_metadata_filter_limits_results(client):
    response = client.post("/search", json={"metadata": {"subject": "Microbiology"}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert _extract_ids(payload) == ["q_5e6f7a8b"]


def test_limit_and_offset_pagination(client):
    response = client.post(
        "/search",
        json={
            "query": "",
            "limit": 1,
            "offset": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 2
    assert payload["pagination"]["offset"] == 1
    assert payload["pagination"]["returned"] == 1
    assert _extract_ids(payload) == ["q_5e6f7a8b"]


def test_filters_endpoint_returns_distinct_facets(client):
    response = client.get("/search/filters")
    assert response.status_code == 200
    payload = response.json()
    assert payload["subjects"] == ["Microbiology", "Pathology"]
    assert payload["systems"] == ["Cardiovascular", "Respiratory"]
    assert payload["statuses"] == ["Unused"]
    assert payload["difficulties"] == ["Easy", "Medium"]
    assert sorted(payload["tags"]) == ["high-yield", "infection", "pediatrics", "vascular"]
