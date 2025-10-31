from __future__ import annotations

import json
from datetime import datetime, timezone

from analytics.cli import run_generation_cycle


def _write_sample_questions(tmp_path):
    data = [
        {
            "id": "q1",
            "metadata": {
                "difficulty": "Easy",
                "status": "Unused",
                "usage_count": 3,
            },
        }
    ]
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_run_generation_cycle_produces_timestamped_artifacts(tmp_path):
    data_dir = tmp_path / "questions"
    data_dir.mkdir()
    _write_sample_questions(data_dir)

    artifact_dir = tmp_path / "analytics"
    docs_markdown = tmp_path / "metrics.md"
    docs_json = tmp_path / "metrics.json"

    fixed_now = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    result = run_generation_cycle(
        data_dir=data_dir,
        artifact_dir=artifact_dir,
        docs_markdown=docs_markdown,
        docs_json=docs_json,
        now=fixed_now,
    )

    assert result["timestamp"] == "20240102T030405Z"
    assert result["generated_at"] == "2024-01-02T03:04:05Z"

    json_path = artifact_dir / "20240102T030405Z.json"
    markdown_path = artifact_dir / "20240102T030405Z.md"
    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["generated_at"] == "2024-01-02T03:04:05Z"
    metrics = payload["metrics"]
    assert metrics["total_questions"] == 1
    assert metrics["difficulty_distribution"] == {"Easy": 1}
    assert metrics["review_status_distribution"] == {"Unused": 1}
    assert metrics["usage_summary"]["total_usage"] == 3

    assert docs_markdown.exists()
    assert docs_json.exists()
    docs_payload = json.loads(docs_json.read_text(encoding="utf-8"))
    assert docs_payload["total_questions"] == 1
