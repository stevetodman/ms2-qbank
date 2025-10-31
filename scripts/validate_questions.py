"""Validate question data files against the MS2 QBank schema."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:  # pragma: no cover - optional dependency guard
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
except ImportError:  # pragma: no cover - handled at runtime
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    JSONSchemaValidationError = None  # type: ignore[assignment]


def load_json(path: Path) -> object:
    """Load JSON from *path* and return the resulting object."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - runtime guard
        raise ValueError(f"{path}: invalid JSON - {exc.msg} (line {exc.lineno} column {exc.colno})") from exc


def create_validator(schema_path: Path) -> "Draft202012Validator":
    """Create a JSON Schema validator for the question schema."""

    if Draft202012Validator is None or FormatChecker is None:
        print(
            "Error: The 'jsonschema' package is required. Install it with `pip install jsonschema`.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    schema_data = load_json(schema_path)
    if not isinstance(schema_data, dict):
        raise SystemExit(f"Error: {schema_path} does not contain a JSON object")

    try:
        return Draft202012Validator(schema_data, format_checker=FormatChecker())
    except JSONSchemaValidationError as exc:  # pragma: no cover - schema authoring guard
        raise SystemExit(f"Error: invalid schema in {schema_path}: {exc.message}") from exc


def iter_question_files(path: Path) -> Iterable[Path]:
    """Yield JSON files under *path*."""

    if path.is_file():
        yield path
    else:
        for json_file in sorted(path.rglob("*.json")):
            if json_file.is_file():
                yield json_file


def build_location(source: Path, index: int, path: Sequence[object]) -> str:
    """Format a human readable location from a JSON schema error path."""

    location = f"{source}[{index}]"
    for element in path:
        if isinstance(element, int):
            location += f"[{element}]"
        else:
            location += f".{element}"
    return location


def _schema_error_sort_key(error: "JSONSchemaValidationError") -> Sequence[str]:
    key: List[str] = []
    for element in error.absolute_path:
        if isinstance(element, int):
            key.append(f"i:{element:08d}")
        else:
            key.append(f"s:{element}")
    key.append(error.message)
    return key


def additional_checks(question: dict, source: Path, index: int) -> List[str]:
    """Perform semantic validations that extend the JSON schema."""

    errors: List[str] = []

    choices = question.get("choices")
    choice_labels = []
    if isinstance(choices, list):
        seen_labels = set()
        for c_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                continue
            label = choice.get("label")
            if isinstance(label, str):
                if label in seen_labels:
                    errors.append(
                        f"{source}[{index}].choices[{c_index}]: duplicate label '{label}'"
                    )
                else:
                    seen_labels.add(label)
                    choice_labels.append(label)
        choice_labels = sorted(seen_labels)

    answer = question.get("answer")
    if isinstance(answer, str) and choice_labels:
        if answer not in choice_labels:
            errors.append(
                f"{source}[{index}]: answer '{answer}' must match one of the available choice labels"
            )

    explanation = question.get("explanation")
    if isinstance(explanation, dict):
        rationales = explanation.get("rationales")
        if isinstance(rationales, list) and choice_labels:
            for r_index, rationale in enumerate(rationales):
                if not isinstance(rationale, dict):
                    continue
                choice_label = rationale.get("choice")
                if isinstance(choice_label, str) and choice_label not in choice_labels:
                    errors.append(
                        f"{source}[{index}].explanation.rationales[{r_index}].choice "
                        f"references unknown label '{choice_label}'"
                    )

    return errors


def validate_file(path: Path, validator: "Draft202012Validator") -> Tuple[int, List[str]]:
    """Validate a single question data file."""

    try:
        data = load_json(path)
    except ValueError as exc:
        return 0, [str(exc)]

    if not isinstance(data, list):
        return 0, [f"{path}: expected a list of question objects"]

    if not data:
        return 0, [f"{path}: expected at least one question"]

    errors: List[str] = []
    for index, question in enumerate(data):
        if not isinstance(question, dict):
            errors.append(f"{path}[{index}]: each entry must be an object")
            continue

        schema_errors = sorted(validator.iter_errors(question), key=_schema_error_sort_key)
        for error in schema_errors:
            location = build_location(path, index, list(error.absolute_path))
            errors.append(f"{location}: {error.message}")

        errors.extend(additional_checks(question, path, index))

    return len(data), errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_path",
        type=Path,
        nargs="?",
        default=Path("data/questions"),
        help="Path to a question JSON file or directory containing JSON files.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("data/schema/question.schema.json"),
        help="Path to the JSON schema describing a question record.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    data_path: Path = args.data_path
    schema_path: Path = args.schema

    if not data_path.exists():
        print(f"Error: {data_path} does not exist", file=sys.stderr)
        return 2

    validator = create_validator(schema_path)

    json_files = [path for path in iter_question_files(data_path) if path.suffix.lower() == ".json"]

    if not json_files:
        print(f"Error: No JSON files found in {data_path}", file=sys.stderr)
        return 2

    results: List[Tuple[Path, int, List[str]]] = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(validate_file, path, validator): path for path in json_files}
        for future in as_completed(futures):
            path = futures[future]
            try:
                count, errors = future.result()
            except Exception as exc:  # pragma: no cover - unexpected runtime failure
                count, errors = 0, [f"{path}: unexpected error: {exc}"]
            results.append((path, count, errors))

    error_map: Dict[Path, List[str]] = defaultdict(list)
    for path, _, errors in results:
        if errors:
            error_map[path].extend(errors)

    if error_map:
        total_errors = sum(len(errors) for errors in error_map.values())
        print(
            f"Validation failed with {total_errors} error(s) across {len(error_map)} file(s):",
            file=sys.stderr,
        )
        for path in sorted(error_map):
            print(f" - {path}: {len(error_map[path])} error(s)", file=sys.stderr)

        print("\nDetailed errors:", file=sys.stderr)
        for path in sorted(error_map):
            for error in error_map[path]:
                print(f" - {error}", file=sys.stderr)
        return 1

    total_questions = sum(count for _, count, _ in results)

    if total_questions == 0:
        print(f"Error: No question records found in {data_path}", file=sys.stderr)
        return 2

    print(
        f"Validation passed for {total_questions} question(s) across {len(json_files)} file(s).",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
