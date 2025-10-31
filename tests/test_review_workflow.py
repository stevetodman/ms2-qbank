from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from reviews import ReviewStore, create_app
from reviews.models import ReviewAction, ReviewEvent, ReviewerRole


def build_client(tmp_path: Path) -> TestClient:
    store = ReviewStore(tmp_path / "reviews.db")
    app = create_app(store)
    return TestClient(app)


def test_review_workflow_persists_history(tmp_path: Path) -> None:
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
        json={
            "reviewer": "Dr. Grey",
            "action": "comment",
            "role": "reviewer",
            "comment": "Needs updated statistics.",
        },
    )
    assert comment_response.status_code == 200
    comment_payload = comment_response.json()
    assert comment_payload["current_status"] == "pending"
    assert len(comment_payload["history"]) == 1
    assert comment_payload["history"][0]["role"] == "reviewer"

    reject_response = client.post(
        f"/questions/{question_id}/reviews",
        json={
            "reviewer": "Dr. Yang",
            "action": "reject",
            "role": "editor",
            "comment": "Incorrect reference cited.",
        },
    )
    assert reject_response.status_code == 200
    reject_payload = reject_response.json()
    assert reject_payload["current_status"] == "rejected"
    assert len(reject_payload["history"]) == 2

    follow_up_response = client.post(
        f"/questions/{question_id}/reviews",
        json={
            "reviewer": "Dr. Karev",
            "action": "comment",
            "role": "admin",
            "comment": "Flagged for audit.",
        },
    )
    assert follow_up_response.status_code == 200
    follow_up_payload = follow_up_response.json()
    assert follow_up_payload["current_status"] == "rejected"
    assert len(follow_up_payload["history"]) == 3
    assert follow_up_payload["history"][2]["role"] == "admin"

    new_client = build_client(tmp_path)
    persisted_response = new_client.get(f"/questions/{question_id}/reviews")
    assert persisted_response.status_code == 200
    persisted_payload = persisted_response.json()
    assert persisted_payload["current_status"] == "rejected"
    assert len(persisted_payload["history"]) == 3
    assert [event["role"] for event in persisted_payload["history"]] == [
        "reviewer",
        "editor",
        "admin",
    ]


def test_comment_requires_text(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_456"

    response = client.post(
        f"/questions/{question_id}/reviews",
        json={"reviewer": "Dr. Bailey", "action": "comment", "role": "reviewer"},
    )
    assert response.status_code == 422


def test_invalid_role_cannot_approve(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_457"

    response = client.post(
        f"/questions/{question_id}/reviews",
        json={
            "reviewer": "Dr. Bailey",
            "action": "approve",
            "role": "reviewer",
            "comment": "Looks good",
        },
    )
    assert response.status_code == 403


def test_invalid_status_transition_returns_conflict(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_458"

    approve_response = client.post(
        f"/questions/{question_id}/reviews",
        json={
            "reviewer": "Dr. Hunt",
            "action": "approve",
            "role": "editor",
            "comment": "Meets publishing standards",
        },
    )
    assert approve_response.status_code == 200

    reject_response = client.post(
        f"/questions/{question_id}/reviews",
        json={
            "reviewer": "Dr. Robbins",
            "action": "reject",
            "role": "editor",
            "comment": "Found issues post-approval",
        },
    )
    assert reject_response.status_code == 409


def test_store_handles_concurrent_appends(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "concurrency.db")
    question_id = "q_concurrency"

    def worker(idx: int) -> None:
        event = ReviewEvent(
            reviewer=f"Reviewer {idx}",
            action=ReviewAction.COMMENT,
            role=ReviewerRole.REVIEWER,
            comment=f"Note {idx}",
        )
        store.append(question_id, event)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(worker, range(20)))

    record = store.get(question_id)
    assert record.current_status() == "pending"
    assert len(record.events) == 20


def test_status_hook_invoked_on_transition(tmp_path: Path) -> None:
    transitions: list[tuple[str, str, str]] = []

    def hook(question_id: str, previous: str, new: str) -> None:
        transitions.append((question_id, previous, new))

    store = ReviewStore(tmp_path / "hook.db", analytics_hook=hook)
    question_id = "q_hook"

    store.append(
        question_id,
        ReviewEvent(
            reviewer="Dr. Webber",
            action=ReviewAction.COMMENT,
            role=ReviewerRole.REVIEWER,
            comment="Initial feedback",
        ),
    )
    assert transitions == []

    store.append(
        question_id,
        ReviewEvent(
            reviewer="Dr. Shepherd",
            action=ReviewAction.APPROVE,
            role=ReviewerRole.EDITOR,
            comment="Cleared for publication",
        ),
    )

    assert transitions == [(question_id, "pending", "approved")]
