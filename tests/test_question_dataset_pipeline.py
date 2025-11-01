from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from questions.pipeline import BuildResult, DatasetBuildError, build_question_dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "data/schema/question.schema.json"
ID_REGEX = re.compile(r"^q_[0-9a-f]{8}$")


def _legacy_question(index: int, *, explicit_id: str | None = None) -> dict:
    question = {
        "prompt": f"Legacy stem {index} about cardiac physiology.",
        "options": [
            f"Choice {index}A",
            f"Choice {index}B",
            f"Choice {index}C",
        ],
        "correct_answer": "A",
        "explanation_text": f"Because option A is correct for question {index}.",
        "answer_explanations": [
            {"choice": "A", "text": "Rationale for A."},
            {"choice": "B", "text": "Rationale for B."},
            {"choice": "C", "text": "Rationale for C."},
        ],
        "subject": "path",
        "system": "cardio",
        "difficulty": "medium",
        "status": "new",
        "tags": ["cardiology", f"tag-{index}"],
    }
    if explicit_id is not None:
        question["id"] = explicit_id
    else:
        question["question_id"] = f"legacy-{index}"
    return question


def _write_legacy_file(path: Path, questions: list[dict]) -> None:
    path.write_text(json.dumps(questions), encoding="utf-8")


def _write_ndjson_file(path: Path, questions: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for question in questions:
            handle.write(json.dumps(question))
            handle.write("\n")


def test_build_question_dataset_chunks_and_validates(tmp_path: Path) -> None:
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()

    batch_one = [_legacy_question(i) for i in range(3)]
    batch_two = [_legacy_question(i + 3) for i in range(2)]

    _write_legacy_file(legacy_dir / "export_a.json", batch_one)
    _write_legacy_file(legacy_dir / "export_b.json", batch_two)

    output_dir = tmp_path / "normalized"
    result = build_question_dataset(
        [legacy_dir],
        output_dir=output_dir,
        chunk_size=2,
        schema_path=SCHEMA_PATH,
        validate=False,
    )

    assert isinstance(result, BuildResult)
    assert result.processed_records == 5
    assert result.migrated_records == 5
    assert result.skipped_records == 0
    assert len(result.output_files) == 3
    assert [path.name for path in result.output_files] == [
        "questions_0001.json",
        "questions_0002.json",
        "questions_0003.json",
    ]
    assert all(path.exists() for path in result.output_files)
    assert result.validation_errors == {}
    assert result.validated_records == 0

    ids: set[str] = set()
    for path in result.output_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for question in data:
            assert ID_REGEX.match(question["id"])
            ids.add(question["id"])
            metadata = question["metadata"]
            assert metadata["subject"] == "Pathology"
            assert metadata["system"] == "Cardiovascular"
            assert metadata["difficulty"] in {"Medium"}
            assert metadata["status"] == "Unused"
            assert metadata["keywords"]

    assert len(ids) == 5
    assert any("canonical id" in note for note in result.notes)

    report_path = output_dir / "build_report.csv"
    assert report_path.exists()
    with report_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    summary = {row["source"]: row for row in rows}
    assert str(legacy_dir / "export_a.json") in summary
    assert str(legacy_dir / "export_b.json") in summary
    assert summary[str(legacy_dir / "export_a.json")]["processed"] == "3"
    assert summary[str(legacy_dir / "export_a.json")]["migrated"] == "3"
    assert summary[str(legacy_dir / "export_a.json")]["skipped"] == "0"


def test_build_question_dataset_deduplicates_ids(tmp_path: Path) -> None:
    legacy_file = tmp_path / "legacy.json"
    questions = [
        _legacy_question(0, explicit_id="q_deadbeef"),
        _legacy_question(1, explicit_id="q_deadbeef"),
    ]
    _write_legacy_file(legacy_file, questions)

    output_dir = tmp_path / "normalized"
    result = build_question_dataset(
        [legacy_file],
        output_dir=output_dir,
        chunk_size=10,
        schema_path=SCHEMA_PATH,
        validate=False,
    )

    all_questions = json.loads(result.output_files[0].read_text(encoding="utf-8"))
    ids = [question["id"] for question in all_questions]

    assert len(ids) == 2
    assert len(set(ids)) == 2
    detection_indices = [
        idx
        for idx, note in enumerate(result.notes)
        if "detected duplicate id 'q_deadbeef'" in note
    ]
    assignment_indices = [
        idx for idx, note in enumerate(result.notes) if "assigned new canonical id" in note
    ]

    assert detection_indices
    assert assignment_indices
    assert detection_indices[0] < assignment_indices[0]


def test_build_question_dataset_streams_ndjson(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    legacy_file = tmp_path / "legacy.ndjson"
    questions = [_legacy_question(i) for i in range(6)]
    _write_ndjson_file(legacy_file, questions)

    def _fail_load_json(*_args, **_kwargs):
        raise AssertionError("load_json should not be used for streaming inputs")

    monkeypatch.setattr("scripts.migrate_questions.load_json", _fail_load_json)

    output_dir = tmp_path / "normalized"
    result = build_question_dataset(
        [legacy_file],
        output_dir=output_dir,
        chunk_size=3,
        schema_path=SCHEMA_PATH,
        validate=False,
    )

    assert result.processed_records == 6
    assert len(result.output_files) == 2
    report_path = output_dir / "build_report.csv"
    assert report_path.exists()
    with report_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["source"] == str(legacy_file)
    assert rows[0]["processed"] == "6"


def test_build_question_dataset_missing_source(tmp_path: Path) -> None:
    with pytest.raises(DatasetBuildError):
        build_question_dataset(
            [tmp_path / "missing.json"],
            output_dir=tmp_path / "out",
            schema_path=SCHEMA_PATH,
        )
