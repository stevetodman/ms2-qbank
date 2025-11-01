from __future__ import annotations

import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("REVIEWS_JWT_SECRET", "test-secret")

import jwt
from fastapi.testclient import TestClient

from reviews import ReviewStore, create_app
from reviews.auth_providers import JWKSProviderConfig
from reviews.models import ReviewAction, ReviewEvent, ReviewerRole

JWT_SECRET = os.environ["REVIEWS_JWT_SECRET"]


def _issue_token(identity: str, roles: list[str]) -> str:
    return jwt.encode({"sub": identity, "roles": roles}, JWT_SECRET, algorithm="HS256")


def auth_headers(identity: str, roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_issue_token(identity, roles)}"}


def build_client(tmp_path: Path, **create_kwargs) -> TestClient:
    store = create_kwargs.pop(
        "store",
        ReviewStore(
            tmp_path / "reviews.db",
            audit_log_path=create_kwargs.pop("audit_log_path", tmp_path / "audit.log"),
        ),
    )
    if "jwt_secret" not in create_kwargs and "jwks_providers" not in create_kwargs:
        create_kwargs["jwt_secret"] = JWT_SECRET
    app = create_app(store, **create_kwargs)
    return TestClient(app)


def _jwks_entry(secret: bytes, kid: str) -> dict[str, str]:
    return {
        "kty": "oct",
        "k": base64.urlsafe_b64encode(secret).rstrip(b"=").decode(),
        "alg": "HS256",
        "kid": kid,
    }


def test_review_workflow_persists_history(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_123"

    response = client.get(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Grey", ["reviewer"]),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "question_id": question_id,
        "current_status": "pending",
        "history": [],
        "allowed_actions": ["comment"],
    }

    comment_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Grey", ["reviewer"]),
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
    assert comment_payload["allowed_actions"] == ["comment"]

    reject_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Yang", ["editor"]),
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
    assert reject_payload["allowed_actions"] == ["comment", "approve", "reject"]

    follow_up_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Karev", ["admin"]),
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
    assert follow_up_payload["allowed_actions"] == ["comment", "approve", "reject"]

    new_client = build_client(tmp_path)
    persisted_response = new_client.get(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Karev", ["admin"]),
    )
    assert persisted_response.status_code == 200
    persisted_payload = persisted_response.json()
    assert persisted_payload["current_status"] == "rejected"
    assert len(persisted_payload["history"]) == 3
    assert [event["role"] for event in persisted_payload["history"]] == [
        "reviewer",
        "editor",
        "admin",
    ]
    assert persisted_payload["allowed_actions"] == ["comment", "approve", "reject"]


def test_comment_requires_text(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_456"

    response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Bailey", ["reviewer"]),
        json={"reviewer": "Dr. Bailey", "action": "comment", "role": "reviewer"},
    )
    assert response.status_code == 422


def test_invalid_role_cannot_approve(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_457"

    response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Bailey", ["reviewer"]),
        json={
            "reviewer": "Dr. Bailey",
            "action": "approve",
            "role": "reviewer",
            "comment": "Looks good",
        },
    )
    assert response.status_code == 403


def test_user_without_editor_role_cannot_approve(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_459"

    response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Stevens", ["reviewer"]),
        json={
            "reviewer": "Dr. Stevens",
            "action": "approve",
            "role": "editor",
            "comment": "Attempting approval without permission",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Authenticated user lacks required role"


def test_invalid_status_transition_returns_conflict(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    question_id = "q_458"

    approve_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Hunt", ["editor"]),
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
        headers=auth_headers("Dr. Robbins", ["editor"]),
        json={
            "reviewer": "Dr. Robbins",
            "action": "reject",
            "role": "editor",
            "comment": "Found issues post-approval",
        },
    )
    assert reject_response.status_code == 409


def test_store_handles_concurrent_appends(tmp_path: Path) -> None:
    store = ReviewStore(tmp_path / "concurrency.db", audit_log_path=tmp_path / "audit.log")
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

    store = ReviewStore(tmp_path / "hook.db", analytics_hook=hook, audit_log_path=tmp_path / "audit.log")
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


def test_multi_issuer_jwt_validation(tmp_path: Path) -> None:
    issuer_one = "https://issuer-one.example"
    issuer_two = "https://issuer-two.example"
    secret_one = b"issuer-one-secret"
    secret_two = b"issuer-two-secret"

    jwks_documents = {
        "https://issuer-one.example/jwks": {"keys": [_jwks_entry(secret_one, "one")]},
        "https://issuer-two.example/jwks": {"keys": [_jwks_entry(secret_two, "two")]},
    }

    def fetcher(url: str):
        return jwks_documents[url]

    providers = [
        JWKSProviderConfig(
            issuer=issuer_one,
            jwks_url="https://issuer-one.example/jwks",
            audience="ms2-qbank",
            role_mapping={"review-editor": "editor"},
        ),
        JWKSProviderConfig(
            issuer=issuer_two,
            jwks_url="https://issuer-two.example/jwks",
            roles_claim="permissions",
            default_roles=("reviewer",),
        ),
    ]

    store = ReviewStore(tmp_path / "jwks.db", audit_log_path=tmp_path / "audit.log")
    client = build_client(
        tmp_path,
        store=store,
        jwks_providers=providers,
        jwks_fetcher=fetcher,
    )

    token_one = jwt.encode(
        {
            "iss": issuer_one,
            "aud": "ms2-qbank",
            "sub": "Editor One",
            "roles": ["review-editor"],
        },
        secret_one,
        algorithm="HS256",
        headers={"kid": "one"},
    )
    response_one = client.get(
        "/questions/q-multi/reviews",
        headers={"Authorization": f"Bearer {token_one}"},
    )
    assert response_one.status_code == 200
    payload_one = response_one.json()
    assert payload_one["allowed_actions"] == ["comment", "approve", "reject"]

    token_two = jwt.encode(
        {
            "iss": issuer_two,
            "sub": "Reviewer Two",
            "permissions": "author reviewer",
        },
        secret_two,
        algorithm="HS256",
        headers={"kid": "two"},
    )
    response_two = client.get(
        "/questions/q-multi/reviews",
        headers={"Authorization": f"Bearer {token_two}"},
    )
    assert response_two.status_code == 200
    payload_two = response_two.json()
    assert payload_two["allowed_actions"] == ["comment"]

    unknown_token = jwt.encode(
        {"iss": "https://unknown-issuer.example", "sub": "User"},
        "unused",
        algorithm="HS256",
    )
    rejected = client.get(
        "/questions/q-multi/reviews",
        headers={"Authorization": f"Bearer {unknown_token}"},
    )
    assert rejected.status_code == 401


def test_audit_log_written_on_state_transition(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.log"
    store = ReviewStore(tmp_path / "audit.db", audit_log_path=audit_path)
    client = build_client(tmp_path, store=store)

    question_id = "q_audit"
    comment_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Wilson", ["reviewer"]),
        json={
            "reviewer": "Dr. Wilson",
            "action": "comment",
            "role": "reviewer",
            "comment": "Initial feedback",
        },
    )
    assert comment_response.status_code == 200
    assert not audit_path.exists()

    approve_response = client.post(
        f"/questions/{question_id}/reviews",
        headers=auth_headers("Dr. Warren", ["editor"]),
        json={
            "reviewer": "Dr. Warren",
            "action": "approve",
            "role": "editor",
            "comment": "Looks good",
        },
    )
    assert approve_response.status_code == 200
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["question_id"] == question_id
    assert entry["previous_status"] == "pending"
    assert entry["new_status"] == "approved"
    assert entry["action"] == "approve"
