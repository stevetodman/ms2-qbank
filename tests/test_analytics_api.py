from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List

import jwt
from fastapi.testclient import TestClient

from analytics.scheduler import AnalyticsRefreshScheduler
from analytics.service import AnalyticsService
import search.app as search_app
from reviews.models import ReviewAction, ReviewEvent, ReviewerRole
from reviews.store import ReviewStore
from reviews.app import create_app

JWT_SECRET = "analytics-test-secret"


def _write_artifact(directory, basename: str, metrics: Dict[str, object], generated_at: str) -> None:
    payload = {"generated_at": generated_at, "metrics": metrics}
    json_path = directory / f"{basename}.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    markdown_path = directory / f"{basename}.md"
    markdown_path.write_text("# metrics\n", encoding="utf-8")


def _issue_token(identity: str = "analytics-tester", roles: List[str] | None = None) -> str:
    payload = {"sub": identity, "roles": roles or ["admin"]}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _auth_headers(identity: str = "analytics-tester", roles: List[str] | None = None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {_issue_token(identity, roles)}"}


def test_latest_analytics_endpoint_returns_latest(tmp_path, monkeypatch):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()

    metrics_old = {
        "total_questions": 1,
        "difficulty_distribution": {"Easy": 1},
        "review_status_distribution": {"Unused": 1},
        "usage_summary": {
            "tracked_questions": 1,
            "total_usage": 3,
            "average_usage": 3.0,
            "minimum_usage": 3,
            "maximum_usage": 3,
            "usage_distribution": {"3": 1},
        },
    }
    _write_artifact(artifact_dir, "20240102T030405Z", metrics_old, "2024-01-02T03:04:05Z")

    metrics_new = {
        "total_questions": 2,
        "difficulty_distribution": {"Medium": 2},
        "review_status_distribution": {"Correct": 2},
        "usage_summary": {
            "tracked_questions": 2,
            "total_usage": 10,
            "average_usage": 5.0,
            "minimum_usage": 4,
            "maximum_usage": 6,
            "usage_distribution": {"3": 5},
        },
    }
    _write_artifact(artifact_dir, "20240203T040506Z", metrics_new, "2024-02-03T04:05:06Z")

    monkeypatch.setattr(search_app, "ANALYTICS_DIRECTORY", artifact_dir)

    with TestClient(search_app.app) as client:
        response = client.get("/analytics/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_at"] == "2024-02-03T04:05:06Z"
    assert payload["artifact"]["json_path"] == "20240203T040506Z.json"
    assert payload["artifact"]["markdown_path"] == "20240203T040506Z.md"
    assert payload["is_fresh"] is False

    metrics = payload["metrics"]
    assert metrics["total_questions"] == 2
    assert metrics["difficulty_distribution"] == {"Medium": 2}
    assert metrics["review_status_distribution"] == {"Correct": 2}

    usage_summary = metrics["usage_summary"]
    assert usage_summary["tracked_questions"] == 2
    assert usage_summary["total_usage"] == 10
    assert usage_summary["minimum_usage"] == 4
    assert usage_summary["maximum_usage"] == 6
    assert usage_summary["usage_distribution"] == [{"deliveries": 3, "questions": 5}]


def test_latest_analytics_endpoint_returns_404_when_missing(tmp_path, monkeypatch):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()
    monkeypatch.setattr(search_app, "ANALYTICS_DIRECTORY", artifact_dir)

    with TestClient(search_app.app) as client:
        response = client.get("/analytics/latest")

    assert response.status_code == 404


def test_latest_analytics_marks_fresh_when_recent(tmp_path, monkeypatch):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()

    metrics = {
        "total_questions": 1,
        "difficulty_distribution": {"Easy": 1},
        "review_status_distribution": {"Approved": 1},
        "usage_summary": {
            "tracked_questions": 1,
            "total_usage": 1,
            "average_usage": 1.0,
            "minimum_usage": 1,
            "maximum_usage": 1,
            "usage_distribution": {"1": 1},
        },
    }
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    _write_artifact(artifact_dir, timestamp, metrics, now.isoformat().replace("+00:00", "Z"))

    monkeypatch.setattr(search_app, "ANALYTICS_DIRECTORY", artifact_dir)

    with TestClient(search_app.app) as client:
        response = client.get("/analytics/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_fresh"] is True


def test_analytics_health_endpoint_reports_fresh_snapshot(tmp_path):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()
    questions_dir = tmp_path / "questions"
    questions_dir.mkdir()

    metrics = _default_metrics_payload()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    _write_artifact(artifact_dir, timestamp, metrics, now.isoformat().replace("+00:00", "Z"))

    scheduler = AnalyticsRefreshScheduler(
        data_dir=questions_dir,
        artifact_dir=artifact_dir,
        docs_markdown=None,
        docs_json=None,
    )
    service = AnalyticsService(
        scheduler=scheduler,
        artifact_dir=artifact_dir,
        check_interval=timedelta(seconds=1),
    )
    store = ReviewStore(tmp_path / "reviews.db")
    app = create_app(store, jwt_secret=JWT_SECRET, analytics_service=service)

    with TestClient(app) as client:
        response = client.get("/analytics/health", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_fresh"] is True
    assert payload["generated_at"] == now.isoformat().replace("+00:00", "Z")


def test_analytics_service_warns_when_snapshot_stale(tmp_path, caplog):
    asyncio.run(_assert_stale_warning(tmp_path, caplog))


async def _assert_stale_warning(tmp_path, caplog) -> None:
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()
    questions_dir = tmp_path / "questions"
    questions_dir.mkdir()

    stale_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    timestamp = stale_time.strftime("%Y%m%dT%H%M%SZ")
    _write_artifact(
        artifact_dir,
        timestamp,
        _default_metrics_payload(),
        stale_time.isoformat().replace("+00:00", "Z"),
    )

    scheduler = AnalyticsRefreshScheduler(
        data_dir=questions_dir,
        artifact_dir=artifact_dir,
        docs_markdown=None,
        docs_json=None,
    )
    service = AnalyticsService(
        scheduler=scheduler,
        artifact_dir=artifact_dir,
        freshness_window=timedelta(minutes=10),
        check_interval=timedelta(milliseconds=50),
    )

    caplog.set_level(logging.WARNING)

    await service.start()
    try:
        await asyncio.sleep(0.2)
    finally:
        await service.shutdown()

    warnings = [record.message for record in caplog.records if record.levelno >= logging.WARNING]
    assert any("Analytics snapshot is stale" in message for message in warnings)


def _build_review_event(action: ReviewAction, role: ReviewerRole, comment: str) -> ReviewEvent:
    return ReviewEvent(reviewer="Tester", action=action, role=role, comment=comment)


async def _await_scheduler_completion(scheduler: AnalyticsRefreshScheduler) -> None:
    for _ in range(50):
        await asyncio.sleep(0.05)
        if scheduler.last_completed_at is not None:
            return
    raise AssertionError("Scheduler did not complete within timeout")


def _default_metrics_payload() -> Dict[str, object]:
    return {
        "total_questions": 1,
        "difficulty_distribution": {"Easy": 1},
        "review_status_distribution": {"Approved": 1},
        "usage_summary": {
            "tracked_questions": 1,
            "total_usage": 1,
            "average_usage": 1.0,
            "minimum_usage": 1,
            "maximum_usage": 1,
            "usage_distribution": {"1": 1},
        },
    }


def _write_artifacts_for_generation(artifact_dir, timestamp: str, payload: Dict[str, object]) -> None:
    json_path = artifact_dir / f"{timestamp}.json"
    markdown_path = artifact_dir / f"{timestamp}.md"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    markdown_path.write_text("# metrics\n", encoding="utf-8")


def test_review_transition_refreshes_analytics(tmp_path, monkeypatch):
    asyncio.run(_exercise_review_transition(tmp_path, monkeypatch))


async def _exercise_review_transition(tmp_path, monkeypatch):
    artifact_dir = tmp_path / "analytics"
    data_dir = tmp_path / "questions"
    artifact_dir.mkdir()
    data_dir.mkdir()

    generated_at_times: List[str] = []

    def fake_runner(data_dir, artifact_dir, docs_markdown=None, docs_json=None):
        moment = datetime.now(timezone.utc)
        timestamp = moment.strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "generated_at": moment.isoformat().replace("+00:00", "Z"),
            "metrics": _default_metrics_payload(),
        }
        _write_artifacts_for_generation(artifact_dir, timestamp, payload)
        generated_at_times.append(payload["generated_at"])
        return {
            "timestamp": timestamp,
            "generated_at": payload["generated_at"],
            "markdown_path": artifact_dir / f"{timestamp}.md",
            "json_path": artifact_dir / f"{timestamp}.json",
            "metrics": payload["metrics"],
        }

    scheduler = AnalyticsRefreshScheduler(
        data_dir=data_dir,
        artifact_dir=artifact_dir,
        docs_markdown=None,
        docs_json=None,
        debounce_seconds=0.05,
        runner=fake_runner,
    )

    await scheduler.start()

    store = ReviewStore(tmp_path / "reviews.db")
    store.set_analytics_hook(scheduler.handle_status_change)

    await asyncio.to_thread(
        store.append,
        "question-1",
        _build_review_event(ReviewAction.COMMENT, ReviewerRole.REVIEWER, "Initial"),
    )
    await asyncio.sleep(0.2)
    assert generated_at_times == []

    await asyncio.to_thread(
        store.append,
        "question-1",
        _build_review_event(ReviewAction.APPROVE, ReviewerRole.EDITOR, "Approved"),
    )

    await _await_scheduler_completion(scheduler)

    assert generated_at_times, "Analytics generation should have been triggered"

    monkeypatch.setattr(search_app, "ANALYTICS_DIRECTORY", artifact_dir)

    with TestClient(search_app.app) as client:
        response = client.get("/analytics/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_fresh"] is True

    await scheduler.shutdown()
