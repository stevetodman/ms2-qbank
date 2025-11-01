from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from library.app import create_app


def get_client() -> TestClient:
    app = create_app(data_dir=Path("data/library"))
    return TestClient(app)


def test_article_search_and_tags() -> None:
    client = get_client()
    response = client.get("/articles", params={"query": "renal"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "renal-pathology"

    tags_response = client.get("/articles/tags")
    assert tags_response.status_code == 200
    assert "cardiology" in tags_response.json()


def test_toggle_article_bookmark() -> None:
    client = get_client()
    response = client.post(
        "/articles/infectious-diseases/bookmark",
        json={"bookmarked": True},
    )
    assert response.status_code == 200
    assert response.json() == {"id": "infectious-diseases", "bookmarked": True}


def test_create_note_and_link_to_review() -> None:
    client = get_client()
    create_response = client.post(
        "/notes",
        json={
            "title": "AKI staging pearls",
            "body": "Track urine output trends and adjust fluids early.",
            "tags": ["nephrology"],
            "article_ids": ["renal-pathology"],
        },
    )
    assert create_response.status_code == 201
    note = create_response.json()

    link_response = client.post(
        f"/notes/{note['id']}/link-review",
        json={"question_id": "question-204"},
    )
    assert link_response.status_code == 200
    linked_note = link_response.json()
    assert "question-204" in linked_note["question_ids"]

    list_response = client.get("/notes", params={"question_id": "question-204"})
    assert list_response.status_code == 200
    notes = list_response.json()
    assert any(item["id"] == note["id"] for item in notes)
