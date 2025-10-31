from __future__ import annotations

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
    )

    assert isinstance(result, BuildResult)
    assert result.processed_records == 5
    assert result.migrated_records == 5
    assert result.skipped_records == 0
    assert len(result.output_files) == 3
    assert all(path.exists() for path in result.output_files)
    assert result.validation_errors == {}
    assert result.validated_records == 5

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
    )

    all_questions = json.loads(result.output_files[0].read_text(encoding="utf-8"))
    ids = [question["id"] for question in all_questions]

    assert len(ids) == 2
    assert len(set(ids)) == 2
    assert any("duplicate id" in note for note in result.notes)


def test_build_question_dataset_missing_source(tmp_path: Path) -> None:
    with pytest.raises(DatasetBuildError):
        build_question_dataset(
            [tmp_path / "missing.json"],
            output_dir=tmp_path / "out",
            schema_path=SCHEMA_PATH,
        )
