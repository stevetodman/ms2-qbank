from __future__ import annotations

import json
from typing import Dict

from fastapi.testclient import TestClient

import search.app as search_app


def _write_artifact(directory, basename: str, metrics: Dict[str, object], generated_at: str) -> None:
    payload = {"generated_at": generated_at, "metrics": metrics}
    json_path = directory / f"{basename}.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    markdown_path = directory / f"{basename}.md"
    markdown_path.write_text("# metrics\n", encoding="utf-8")


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
