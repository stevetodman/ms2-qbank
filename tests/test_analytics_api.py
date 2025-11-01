from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from fastapi import FastAPI
from fastapi.testclient import TestClient

from analytics.scheduler import AnalyticsRefreshScheduler
from analytics.service import AnalyticsService
import search.app as search_app
from reviews.models import ReviewAction, ReviewEvent, ReviewerRole
from reviews.store import ReviewStore


def _write_artifact(directory, basename: str, metrics: Dict[str, object], generated_at: str) -> None:
    payload = {"generated_at": generated_at, "metrics": metrics}
    json_path = directory / f"{basename}.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    markdown_path = directory / f"{basename}.md"
    markdown_path.write_text("# metrics\n", encoding="utf-8")


def _build_service_app(service: AnalyticsService) -> FastAPI:
    app = FastAPI()
    app.include_router(service.router)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - exercised via TestClient
        await service.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - exercised via TestClient
        await service.shutdown()

    return app


def test_analytics_health_endpoint_reports_latest_snapshot(tmp_path):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()
    metrics = {"total_questions": 42}
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    generated_at = now.isoformat().replace("+00:00", "Z")
    _write_artifact(artifact_dir, timestamp, metrics, generated_at)

    service = AnalyticsService(artifact_dir=artifact_dir, check_interval=0.05)
    app = _build_service_app(service)

    with TestClient(app) as client:
        response = client.get("/analytics/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_fresh"] is True
    assert payload["latest_generated_at"] == generated_at


def test_analytics_health_logs_warning_for_stale_snapshot(tmp_path, caplog):
    artifact_dir = tmp_path / "analytics"
    artifact_dir.mkdir()
    metrics = {"total_questions": 1}
    old = datetime.now(timezone.utc) - timedelta(minutes=30)
    timestamp = old.strftime("%Y%m%dT%H%M%SZ")
    generated_at = old.isoformat().replace("+00:00", "Z")
    _write_artifact(artifact_dir, timestamp, metrics, generated_at)

    service = AnalyticsService(artifact_dir=artifact_dir, check_interval=0.05)
    caplog.set_level("WARNING")

    async def _exercise() -> None:
        await service.start()
        await service.shutdown()

    asyncio.run(_exercise())

    assert "No fresh analytics snapshot found" in caplog.text


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
