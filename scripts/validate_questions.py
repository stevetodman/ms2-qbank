"""Validate question data files for schema compliance and metadata coverage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

ID_PATTERN = re.compile(r"^q_[0-9a-f]{8}$")
CHOICE_LABEL_PATTERN = re.compile(r"^[A-Z]$")

SUBJECTS = {
    "Anatomy",
    "Behavioral Science",
    "Biochemistry",
    "Biostatistics",
    "Immunology",
    "Microbiology",
    "Pathology",
    "Pharmacology",
    "Physiology",
}

SYSTEMS = {
    "Cardiovascular",
    "Endocrine",
    "Gastrointestinal",
    "Hematologic/Lymphatic",
    "Musculoskeletal",
    "Nervous",
    "Renal",
    "Reproductive",
    "Respiratory",
    "Skin/Connective Tissue",
    "Multisystem",
}

DIFFICULTIES = {"Easy", "Medium", "Hard"}
STATUSES = {"Unused", "Marked", "Incorrect", "Correct", "Omitted"}
MEDIA_TYPES = {"image", "audio", "video"}


class ValidationError(Exception):
    """Raised when validation fails for a question file."""


def load_questions(path: Path) -> List[dict]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - runtime guard
        raise ValidationError(f"{path}: invalid JSON - {exc}") from exc

    if not isinstance(data, list):
        raise ValidationError(f"{path}: expected an array of question objects")
    return data


def validate_question(question: dict, index: int, source: Path) -> List[str]:
    errors: List[str] = []

    def require(field: str) -> None:
        if field not in question:
            errors.append(f"{source}[{index}]: missing required field '{field}'")

    require("id")
    require("stem")
    require("choices")
    require("answer")
    require("explanation")
    require("metadata")

    qid = question.get("id")
    if not isinstance(qid, str) or not ID_PATTERN.match(qid or ""):
        errors.append(f"{source}[{index}]: 'id' must match pattern ^q_[0-9a-f]{{8}}$")

    stem = question.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        errors.append(f"{source}[{index}]: 'stem' must be a non-empty string")

    choices = question.get("choices")
    if not isinstance(choices, list) or len(choices) < 2:
        errors.append(f"{source}[{index}]: 'choices' must be an array with at least two options")
    else:
        labels_seen = set()
        for c_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                errors.append(f"{source}[{index}].choices[{c_index}]: must be an object")
                continue
            label = choice.get("label")
            text = choice.get("text")
            if not isinstance(label, str) or not CHOICE_LABEL_PATTERN.match(label or ""):
                errors.append(
                    f"{source}[{index}].choices[{c_index}]: 'label' must be a single capital letter"
                )
            elif label in labels_seen:
                errors.append(
                    f"{source}[{index}].choices[{c_index}]: duplicate label '{label}'"
                )
            else:
                labels_seen.add(label)
            if not isinstance(text, str) or not text.strip():
                errors.append(
                    f"{source}[{index}].choices[{c_index}]: 'text' must be a non-empty string"
                )

    answer = question.get("answer")
    if not isinstance(answer, str) or not CHOICE_LABEL_PATTERN.match(answer or ""):
        errors.append(f"{source}[{index}]: 'answer' must be a capital letter")
    elif choices and isinstance(choices, list):
        choice_labels = {choice.get("label") for choice in choices if isinstance(choice, dict)}
        if answer not in choice_labels:
            errors.append(
                f"{source}[{index}]: 'answer' '{answer}' must correspond to one of the provided choices"
            )

    explanation = question.get("explanation")
    if not isinstance(explanation, dict):
        errors.append(f"{source}[{index}]: 'explanation' must be an object")
    else:
        summary = explanation.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"{source}[{index}]: explanation.summary must be a non-empty string")
        rationales = explanation.get("rationales")
        if rationales is not None:
            if not isinstance(rationales, list):
                errors.append(
                    f"{source}[{index}]: explanation.rationales must be an array when provided"
                )
            else:
                for r_index, rationale in enumerate(rationales):
                    if not isinstance(rationale, dict):
                        errors.append(
                            f"{source}[{index}]: explanation.rationales[{r_index}] must be an object"
                        )
                        continue
                    r_choice = rationale.get("choice")
                    r_text = rationale.get("text")
                    if not isinstance(r_choice, str) or not CHOICE_LABEL_PATTERN.match(r_choice or ""):
                        errors.append(
                            f"{source}[{index}]: explanation.rationales[{r_index}].choice must be a capital letter"
                        )
                    if not isinstance(r_text, str) or not r_text.strip():
                        errors.append(
                            f"{source}[{index}]: explanation.rationales[{r_index}].text must be a non-empty string"
                        )

    metadata = question.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{source}[{index}]: 'metadata' must be an object")
    else:
        for field in ("subject", "system", "difficulty", "status", "keywords"):
            if field not in metadata:
                errors.append(f"{source}[{index}]: metadata missing required field '{field}'")

        subject = metadata.get("subject")
        if subject not in SUBJECTS:
            errors.append(
                f"{source}[{index}]: metadata.subject must be one of {sorted(SUBJECTS)}"
            )

        system = metadata.get("system")
        if system not in SYSTEMS:
            errors.append(
                f"{source}[{index}]: metadata.system must be one of {sorted(SYSTEMS)}"
            )

        difficulty = metadata.get("difficulty")
        if difficulty not in DIFFICULTIES:
            errors.append(
                f"{source}[{index}]: metadata.difficulty must be one of {sorted(DIFFICULTIES)}"
            )

        status = metadata.get("status")
        if status not in STATUSES:
            errors.append(
                f"{source}[{index}]: metadata.status must be one of {sorted(STATUSES)}"
            )

        keywords = metadata.get("keywords")
        if not isinstance(keywords, list) or not keywords:
            errors.append(
                f"{source}[{index}]: metadata.keywords must be a non-empty array of strings"
            )
        else:
            for kw_index, keyword in enumerate(keywords):
                if not isinstance(keyword, str) or not keyword.strip():
                    errors.append(
                        f"{source}[{index}]: metadata.keywords[{kw_index}] must be a non-empty string"
                    )

        media = metadata.get("media")
        if media is not None:
            if not isinstance(media, list):
                errors.append(f"{source}[{index}]: metadata.media must be an array when provided")
            else:
                for m_index, item in enumerate(media):
                    if not isinstance(item, dict):
                        errors.append(
                            f"{source}[{index}]: metadata.media[{m_index}] must be an object"
                        )
                        continue
                    media_type = item.get("type")
                    uri = item.get("uri")
                    if media_type not in MEDIA_TYPES:
                        errors.append(
                            f"{source}[{index}]: metadata.media[{m_index}].type must be one of {sorted(MEDIA_TYPES)}"
                        )
                    if not isinstance(uri, str) or not uri.strip():
                        errors.append(
                            f"{source}[{index}]: metadata.media[{m_index}].uri must be a non-empty string"
                        )
                    alt_text = item.get("alt_text")
                    if alt_text is not None and not isinstance(alt_text, str):
                        errors.append(
                            f"{source}[{index}]: metadata.media[{m_index}].alt_text must be a string when provided"
                        )

        references = metadata.get("references")
        if references is not None:
            if not isinstance(references, list):
                errors.append(
                    f"{source}[{index}]: metadata.references must be an array when provided"
                )
            else:
                for r_index, ref in enumerate(references):
                    if not isinstance(ref, dict):
                        errors.append(
                            f"{source}[{index}]: metadata.references[{r_index}] must be an object"
                        )
                        continue
                    for field in ("title", "source"):
                        if field not in ref or not isinstance(ref[field], str) or not ref[field].strip():
                            errors.append(
                                f"{source}[{index}]: metadata.references[{r_index}].{field} must be a non-empty string"
                            )
                    url = ref.get("url")
                    if url is not None and (not isinstance(url, str) or not url.strip()):
                        errors.append(
                            f"{source}[{index}]: metadata.references[{r_index}].url must be a non-empty string when provided"
                        )

    tags = question.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            errors.append(f"{source}[{index}]: 'tags' must be an array when provided")
        else:
            for t_index, tag in enumerate(tags):
                if not isinstance(tag, str) or not tag.strip():
                    errors.append(
                        f"{source}[{index}]: tags[{t_index}] must be a non-empty string"
                    )

    return errors


def validate_file(path: Path) -> Tuple[int, List[str]]:
    questions = load_questions(path)
    errors: List[str] = []
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            errors.append(f"{path}[{index}]: each entry must be an object")
            continue
        errors.extend(validate_question(question, index, path))
    return len(questions), errors


def iter_question_files(data_path: Path) -> Iterable[Path]:
    if data_path.is_file():
        yield data_path
    else:
        yield from sorted(data_path.glob("*.json"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_path",
        type=Path,
        default=Path("data/questions"),
        nargs="?",
        help="Path to a question JSON file or directory containing JSON files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_path: Path = args.data_path

    if not data_path.exists():
        print(f"Error: {data_path} does not exist", file=sys.stderr)
        return 2

    total_questions = 0
    all_errors: List[str] = []

    for path in iter_question_files(data_path):
        if path.suffix.lower() != ".json":
            continue
        count, errors = validate_file(path)
        total_questions += count
        all_errors.extend(errors)

    if total_questions == 0:
        print(f"Error: No question records found in {data_path}", file=sys.stderr)
        return 2

    if all_errors:
        print("Validation failed:")
        for error in all_errors:
            print(f" - {error}")
        return 1

    print(f"Validation passed for {total_questions} question(s) across {data_path}.")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
