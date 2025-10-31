"""Utilities for migrating and validating large question datasets."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import migrate_questions as mq
from scripts import validate_questions as vq
DEFAULT_SCHEMA_PATH = ROOT_DIR / "data/schema/question.schema.json"
ID_PATTERN = re.compile(r"^q_[0-9a-f]{8}$")


@dataclass(slots=True)
class BuildResult:
    """Summary of a dataset build run."""

    input_files: List[Path]
    processed_records: int
    migrated_records: int
    skipped_records: int
    output_files: List[Path]
    notes: List[str]
    validation_errors: Dict[Path, List[str]]
    validated_records: int
    dry_run: bool

    @property
    def chunk_count(self) -> int:
        """Estimated number of output chunks that would be produced."""

        if not self.migrated_records:
            return 0
        if not self.output_files:
            return 0
        return len(self.output_files)


class DatasetBuildError(RuntimeError):
    """Raised when the dataset build cannot produce a valid result."""

    def __init__(self, message: str, result: BuildResult | None = None) -> None:
        super().__init__(message)
        self.result = result


def build_question_dataset(
    sources: Sequence[Path],
    *,
    output_dir: Path,
    chunk_size: int = 500,
    dry_run: bool = False,
    schema_path: Path | None = None,
    validate: bool = True,
    clean: bool = True,
    raise_on_validation_error: bool = True,
) -> BuildResult:
    """Normalise legacy exports into chunked dataset artifacts.

    Parameters
    ----------
    sources:
        Paths to legacy export files or directories containing JSON files.
    output_dir:
        Directory where normalised chunks will be written.
    chunk_size:
        Maximum number of questions per output file.
    dry_run:
        When ``True`` the migration plan is calculated but no files are written.
    schema_path:
        Path to the JSON schema used for validation. Defaults to the repository
        schema when not provided.
    validate:
        Whether to run schema validation against the generated chunks.
    clean:
        Delete existing JSON files in ``output_dir`` before writing new ones.
    raise_on_validation_error:
        When ``True`` a :class:`DatasetBuildError` is raised if validation finds
        any issues. Set to ``False`` to collect the errors in the returned
        result instead.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    files = list(_iter_input_files(sources))
    if not files:
        raise DatasetBuildError("No legacy export files were found to process.")

    schema_location = schema_path if schema_path is not None else DEFAULT_SCHEMA_PATH

    notes: List[str] = []
    seen_ids: set[str] = set()
    processed = 0
    migrated = 0
    skipped = 0
    chunk: List[dict] = []
    output_files: List[Path] = []

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        if clean:
            for existing in sorted(output_dir.glob("*.json")):
                existing.unlink()

    def flush_chunk() -> None:
        nonlocal chunk
        if not chunk:
            return

        chunk_index = len(output_files) + 1
        target = output_dir / f"questions_{chunk_index:04d}.json"
        if dry_run:
            notes.append(f"would write {len(chunk)} question(s) to {target}")
        else:
            mq.dump_json(target, chunk)
        output_files.append(target)
        chunk = []

    for source in files:
        payload = mq.load_json(source)
        if not isinstance(payload, list):
            raise DatasetBuildError(f"{source}: expected a list of question objects")

        for index, entry in enumerate(payload):
            processed += 1
            location = f"{source}[{index}]"

            if not isinstance(entry, dict):
                skipped += 1
                notes.append(f"{location}: skipped non-object entry")
                continue

            question = entry
            changed, operations = mq.migrate_question(question)
            if operations:
                notes.extend(f"{location}: {op}" for op in operations)

            id_note = _ensure_canonical_id(question, seen_ids)
            if id_note:
                notes.append(f"{location}: {id_note}")

            migrated += 1
            chunk.append(question)

            if len(chunk) >= chunk_size:
                flush_chunk()

    flush_chunk()

    validation_errors: Dict[Path, List[str]] = {}
    validated_records = 0

    if validate and not dry_run and output_files:
        try:
            validator = vq.create_validator(schema_location)
        except SystemExit as exc:  # pragma: no cover - dependency guard
            raise DatasetBuildError(
                "jsonschema is required to validate the generated dataset",
            ) from exc

        for path in output_files:
            count, errors = vq.validate_file(path, validator)
            validated_records += count
            if errors:
                validation_errors[path] = errors

    result = BuildResult(
        input_files=files,
        processed_records=processed,
        migrated_records=migrated,
        skipped_records=skipped,
        output_files=output_files,
        notes=notes,
        validation_errors=validation_errors,
        validated_records=validated_records,
        dry_run=dry_run,
    )

    if validation_errors and raise_on_validation_error:
        total_errors = sum(len(errs) for errs in validation_errors.values())
        raise DatasetBuildError(
            f"Validation failed with {total_errors} error(s) across {len(validation_errors)} file(s).",
            result,
        )

    return result


def _iter_input_files(paths: Sequence[Path]) -> Iterator[Path]:
    seen: Dict[Path, None] = {}
    for raw in paths:
        path = raw if isinstance(raw, Path) else Path(raw)
        if path.is_dir():
            for candidate in sorted(path.rglob("*.json")):
                if candidate.is_file():
                    seen.setdefault(candidate.resolve(), None)
        elif path.is_file():
            seen.setdefault(path.resolve(), None)
        else:
            raise DatasetBuildError(f"{path}: not found")
    for path in sorted(seen.keys()):
        yield path


def _ensure_canonical_id(question: dict, seen_ids: set[str]) -> str | None:
    raw_id = question.get("id")
    note: str | None = None

    if isinstance(raw_id, str) and ID_PATTERN.fullmatch(raw_id):
        if raw_id not in seen_ids:
            seen_ids.add(raw_id)
            return None
        note = f"duplicate id '{raw_id}' detected; assigning new canonical id"
    elif isinstance(raw_id, str) and raw_id:
        note = f"replaced non-conforming id '{raw_id}' with canonical id"
    else:
        note = "assigned canonical id"

    canonical_id = _generate_canonical_id(question, seen_ids)
    question["id"] = canonical_id
    seen_ids.add(canonical_id)

    if note:
        note = f"{note} {canonical_id}"

    return note


def _generate_canonical_id(question: dict, seen_ids: set[str]) -> str:
    base_payload = _canonical_id_payload(question)
    counter = 0
    while True:
        digest = hashlib.blake2s(
            f"{base_payload}|{counter}".encode("utf-8"),
            digest_size=4,
        ).hexdigest()
        candidate = f"q_{digest}"
        if candidate not in seen_ids:
            return candidate
        counter += 1


def _canonical_id_payload(question: dict) -> str:
    stem = question.get("stem")
    if not isinstance(stem, str):
        stem = ""

    choices_payload: List[Dict[str, str]] = []
    choices = question.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            label = choice.get("label")
            text = choice.get("text")
            payload_entry = {
                "label": str(label).strip().upper() if isinstance(label, str) else "",
                "text": str(text).strip() if isinstance(text, str) else "",
            }
            choices_payload.append(payload_entry)

    payload = {"stem": stem.strip(), "choices": choices_payload}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)
