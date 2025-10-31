from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from reviews import ReviewStore, create_app


def build_client(tmp_path: Path) -> TestClient:
    store = ReviewStore(tmp_path / "reviews.json")
    app = create_app(store)
    return TestClient(app)


def test_review_workflow_persists_history(tmp_path):
    client = build_client(tmp_path)
    question_id = "q_123"

    response = client.get(f"/questions/{question_id}/reviews")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "question_id": question_id,
        "current_status": "pending",
        "history": [],
    }

    comment_response = client.post(
        f"/questions/{question_id}/reviews",
        json={"reviewer": "Dr. Grey", "action": "comment", "comment": "Needs updated statistics."},
    )
    assert comment_response.status_code == 200
    comment_payload = comment_response.json()
    assert comment_payload["current_status"] == "pending"
    assert len(comment_payload["history"]) == 1
    assert comment_payload["history"][0]["comment"] == "Needs updated statistics."

    approve_response = client.post(
        f"/questions/{question_id}/reviews",
        json={"reviewer": "Dr. Yang", "action": "approve", "comment": "Looks good."},
    )
    assert approve_response.status_code == 200
    approve_payload = approve_response.json()
    assert approve_payload["current_status"] == "approved"
    assert len(approve_payload["history"]) == 2

    reject_response = client.post(
        f"/questions/{question_id}/reviews",
        json={"reviewer": "Dr. Karev", "action": "reject", "comment": "Incorrect diagnosis."},
    )
    assert reject_response.status_code == 200
    reject_payload = reject_response.json()
    assert reject_payload["current_status"] == "rejected"
    assert len(reject_payload["history"]) == 3

    new_client = build_client(tmp_path)
    persisted_response = new_client.get(f"/questions/{question_id}/reviews")
    assert persisted_response.status_code == 200
    persisted_payload = persisted_response.json()
    assert persisted_payload["current_status"] == "rejected"
    assert len(persisted_payload["history"]) == 3


def test_comment_requires_text(tmp_path):
    client = build_client(tmp_path)
    question_id = "q_456"

    response = client.post(
        f"/questions/{question_id}/reviews",
        json={"reviewer": "Dr. Bailey", "action": "comment"},
    )
    assert response.status_code == 422
