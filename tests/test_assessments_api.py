from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from assessments import create_app


class StubAnalyticsHook:
    def __init__(self) -> None:
        self.events = []

    def assessment_completed(self, event) -> None:  # type: ignore[override]
        self.events.append(event)


@pytest.fixture()
def analytics_hook() -> StubAnalyticsHook:
    return StubAnalyticsHook()


@pytest.fixture()
def client(sample_questions, analytics_hook):
    app = create_app(questions=sample_questions, question_count=2, analytics_hook=analytics_hook)
    with TestClient(app) as test_client:
        yield test_client


def test_assessment_lifecycle(sample_questions, client: TestClient, analytics_hook: StubAnalyticsHook):
    payload = {
        "candidate_id": "candidate-123",
        "subject": sample_questions[0]["metadata"]["subject"],
        "system": None,
        "difficulty": None,
        "tags": [],
        "time_limit_minutes": 60,
    }

    response = client.post("/assessments", json=payload)
    assert response.status_code == 200
    created = response.json()
    assessment_id = created["assessment_id"]
    assert created["question_count"] == 2
    assert created["status"] == "created"

    response = client.post(f"/assessments/{assessment_id}/start")
    assert response.status_code == 200
    started = response.json()
    assert started["assessment_id"] == assessment_id
    assert len(started["questions"]) == 2
    assert started["time_limit_seconds"] == 60 * 60

    questions = started["questions"]
    answers = []
    for index, question in enumerate(questions):
        if index == 0:
            answers.append({"question_id": question["id"], "answer": sample_questions[0]["answer"]})
        else:
            answers.append({"question_id": question["id"], "answer": None})

    response = client.post(f"/assessments/{assessment_id}/submit", json={"responses": answers})
    assert response.status_code == 200
    submitted = response.json()
    assert submitted["assessment_id"] == assessment_id
    score = submitted["score"]
    assert score["total_questions"] == 2
    assert score["correct"] == 1
    assert score["incorrect"] == 0
    assert score["omitted"] == 1
    assert pytest.approx(score["percentage"], rel=1e-5) == 50.0
    assert score["duration_seconds"] is not None

    response = client.get(f"/assessments/{assessment_id}/score")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["assessment_id"] == assessment_id
    assert retrieved["score"] == score

    assert len(analytics_hook.events) == 1
    event = analytics_hook.events[0]
    assert event.assessment_id == assessment_id
    assert event.candidate_id == "candidate-123"
    assert event.correct_count == 1
    assert event.incorrect_count == 0
    assert event.omitted_count == 1
    assert event.score_percent == pytest.approx(50.0)
    assert isinstance(event.completed_at, datetime)


def test_start_rejects_when_filters_match_no_questions(client: TestClient):
    response = client.post(
        "/assessments",
        json={
            "candidate_id": "candidate-456",
            "subject": "Nonexistent",
            "system": None,
            "difficulty": None,
            "tags": [],
            "time_limit_minutes": 60,
        },
    )
    assert response.status_code == 200
    assessment_id = response.json()["assessment_id"]

    response = client.post(f"/assessments/{assessment_id}/start")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "No questions match" in detail


def test_score_endpoint_requires_completion(client: TestClient):
    response = client.post(
        "/assessments",
        json={
            "candidate_id": "candidate-789",
            "subject": None,
            "system": None,
            "difficulty": None,
            "tags": [],
            "time_limit_minutes": 60,
        },
    )
    assessment_id = response.json()["assessment_id"]

    response = client.get(f"/assessments/{assessment_id}/score")
    assert response.status_code == 409
    assert response.json()["detail"] == "Assessment has not been submitted"
