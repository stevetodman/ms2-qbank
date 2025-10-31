"""Migrate legacy question records to the current MS2 QBank schema.

The migration performs three primary tasks:

* Normalises legacy field names (e.g. ``question_id`` -> ``id``) and data
  structures (e.g. ``options`` -> ``choices``).
* Ensures the ``metadata`` block is populated with schema-compliant values,
  deriving sensible defaults when legacy data is incomplete.
* Removes deprecated or legacy-prefixed attributes so downstream validators
  only see the supported contract.

For large legacy exports (``.json`` arrays or JSON Lines ``.jsonl`` files) the
script streams the input, writes sharded output files of ``--shard-size``
records to ``--output-dir`` (``data/questions`` by default), and reports the
normalisation work that would be performed. Example::

    python scripts/migrate_questions.py legacy/questions.jsonl \
        --output-dir data/questions --shard-size 250

Use ``--dry-run`` to preview the planned changes without touching the files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from string import ascii_uppercase
from typing import Callable, Iterable, Iterator, List, Sequence
from typing import TextIO


SUBJECT_CHOICES = {
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

SYSTEM_CHOICES = {
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

DIFFICULTY_CHOICES = {"Easy", "Medium", "Hard"}
STATUS_CHOICES = {"Unused", "Marked", "Incorrect", "Correct", "Omitted"}


SUBJECT_SYNONYMS = {
    "behavioural science": "Behavioral Science",
    "behavioral sciences": "Behavioral Science",
    "biostats": "Biostatistics",
    "biostat": "Biostatistics",
    "biostatistics & epidemiology": "Biostatistics",
    "immunology & microbiology": "Immunology",
    "micro": "Microbiology",
    "microbiology & immunology": "Microbiology",
    "path": "Pathology",
    "pathophysiology": "Pathology",
    "pharm": "Pharmacology",
    "phys": "Physiology",
}

SYSTEM_SYNONYMS = {
    "cardio": "Cardiovascular",
    "cv": "Cardiovascular",
    "cardiovascular system": "Cardiovascular",
    "endocrinology": "Endocrine",
    "gi": "Gastrointestinal",
    "gi/nutrition": "Gastrointestinal",
    "hematology": "Hematologic/Lymphatic",
    "heme": "Hematologic/Lymphatic",
    "lymphatic": "Hematologic/Lymphatic",
    "msk": "Musculoskeletal",
    "musculoskeletal system": "Musculoskeletal",
    "neuro": "Nervous",
    "neuro/special senses": "Nervous",
    "renal/urinary": "Renal",
    "repro": "Reproductive",
    "reproductive system": "Reproductive",
    "pulmonary": "Respiratory",
    "respiratory system": "Respiratory",
    "derm": "Skin/Connective Tissue",
    "skin": "Skin/Connective Tissue",
    "multi-system": "Multisystem",
    "multisystem disorders": "Multisystem",
}

DIFFICULTY_SYNONYMS = {
    "low": "Easy",
    "easy": "Easy",
    "medium": "Medium",
    "moderate": "Medium",
    "normal": "Medium",
    "average": "Medium",
    "high": "Hard",
    "hard": "Hard",
    "difficult": "Hard",
}

STATUS_SYNONYMS = {
    "new": "Unused",
    "unused": "Unused",
    "fresh": "Unused",
    "flagged": "Marked",
    "marked": "Marked",
    "review": "Marked",
    "incorrect": "Incorrect",
    "wrong": "Incorrect",
    "correct": "Correct",
    "answered": "Correct",
    "omitted": "Omitted",
    "skipped": "Omitted",
}

DEPRECATED_PREFIXES = ("legacy_", "deprecated_", "old_")
DEPRECATED_FIELDS = {
    "topic",
    "organ_system",
    "difficulty_level",
    "status_text",
    "tags_legacy",
    "notes",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "with",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        default=None,
        help=(
            "Path to a legacy question export (JSON array/JSONL file or directory). "
            "Defaults to the canonical data/questions directory."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/questions"),
        help="Directory where sharded JSON files will be written.",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=250,
        help="Number of questions to include per output shard.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the planned changes without writing to disk.",
    )
    return parser.parse_args(argv)


SUPPORTED_EXTENSIONS = {".json", ".jsonl", ".ndjson"}


def iter_legacy_sources(path: Path) -> Iterator[Path]:
    """Yield JSON/JSONL source files in a stable order."""

    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
        yield path
        return

    if not path.exists():
        return

    for candidate in sorted(path.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield candidate


def load_json(path: Path) -> object:
    """Load JSON from *path* and return the resulting object."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - runtime safety
        raise ValueError(
            f"{path}: invalid JSON - {exc.msg} (line {exc.lineno} column {exc.colno})"
        ) from exc


def dump_json(path: Path, data: object) -> None:
    """Write *data* to *path* with canonical formatting."""

    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def iter_questions_from_file(path: Path) -> Iterator[dict]:
    """Yield question-like objects from *path* without loading everything into memory."""

    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:  # pragma: no cover - runtime guard
                    raise ValueError(
                        f"{path}:{line_no}: invalid JSON - {exc.msg} (line {exc.lineno} column {exc.colno})"
                    ) from exc
                if isinstance(payload, dict):
                    yield payload
                else:
                    continue
        return

    # ``.json`` exports may be arrays or nested objects containing arrays.
    if suffix == ".json":
        first_char = peek_first_non_whitespace(path)
        if first_char == "[":
            with path.open("r", encoding="utf-8") as handle:
                yield from iter_json_array_stream(handle, path)
            return

        payload = load_json(path)
        question_list = extract_question_sequence(payload)
        if question_list is None:
            raise ValueError(f"{path}: unable to locate a question list in the JSON payload")
        for item in question_list:
            if isinstance(item, dict):
                yield item
        return

    raise ValueError(f"{path}: unsupported file extension '{suffix}'")


def peek_first_non_whitespace(path: Path) -> str | None:
    with path.open("r", encoding="utf-8") as handle:
        while True:
            char = handle.read(1)
            if not char:
                return None
            if not char.isspace():
                return char


def iter_json_array_stream(handle: TextIO, source: Path) -> Iterator[dict]:
    """Incrementally parse a JSON array from *handle* and yield dict entries."""

    decoder = json.JSONDecoder()
    buffer = ""
    index = 0
    array_started = False

    while True:
        if index >= len(buffer):
            chunk = handle.read(65536)
            if not chunk:
                if array_started and buffer.strip() in {"", "]"}:
                    return
                if not array_started and not buffer.strip():
                    return
                raise ValueError(f"{source}: unexpected end of file while reading array")
            buffer = buffer[index:] + chunk if index < len(buffer) else chunk
            index = 0
            continue

        if not array_started:
            char = buffer[index]
            if char.isspace():
                index += 1
                continue
            if char != "[":
                raise ValueError(f"{source}: expected JSON array at top level")
            array_started = True
            index += 1
            continue

        char = buffer[index]
        if char in " \t\r\n,":
            index += 1
            continue
        if char == "]":
            return

        try:
            obj, offset = decoder.raw_decode(buffer[index:])
        except json.JSONDecodeError:
            chunk = handle.read(65536)
            if not chunk:
                raise ValueError(f"{source}: truncated JSON value inside array")
            buffer = buffer[index:] + chunk
            index = 0
            continue

        if isinstance(obj, dict):
            yield obj

        index += offset
        if index > 4096:
            buffer = buffer[index:]
            index = 0


def extract_question_sequence(payload: object) -> list[dict] | None:
    """Locate the first list of dict-like objects within *payload*."""

    if isinstance(payload, list):
        if payload and all(isinstance(item, dict) for item in payload):
            return payload
        if not payload:
            return []

    if isinstance(payload, dict):
        for key in ("questions", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
        for value in payload.values():
            candidate = extract_question_sequence(value)
            if candidate is not None:
                return candidate

    return None


class QuestionShardWriter:
    """Utility to collect migrated questions and persist them to sharded files."""

    def __init__(self, output_dir: Path, shard_size: int, *, dry_run: bool = False) -> None:
        if shard_size <= 0:
            raise ValueError("shard_size must be a positive integer")
        self.output_dir = output_dir
        self.shard_size = shard_size
        self.dry_run = dry_run
        self._buffer: list[dict] = []
        self._shard_index = 1
        self.emitted_paths: list[Path] = []
        self.total_written = 0

    def add(self, question: dict) -> None:
        self._buffer.append(question)
        self.total_written += 1
        if len(self._buffer) >= self.shard_size:
            self._flush()

    def finalize(self) -> list[Path]:
        self._flush()
        return self.emitted_paths

    def _flush(self) -> None:
        if not self._buffer:
            return

        shard_name = f"questions_{self._shard_index:04d}.json"
        path = self.output_dir / shard_name
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            dump_json(path, list(self._buffer))
        self.emitted_paths.append(path)
        self._buffer.clear()
        self._shard_index += 1


def migrate_question(question: dict) -> tuple[bool, List[str]]:
    """Transform a single question object in place."""

    changed = False
    operations: List[str] = []

    def record(operation: str) -> None:
        nonlocal changed
        changed = True
        operations.append(operation)

    # --- Field normalisation -------------------------------------------------
    set_if_missing(question, "id", question, ("question_id", "legacy_id"), record)
    set_if_missing(question, "stem", question, ("prompt", "question", "body"), record)

    if "choices" not in question:
        legacy_choices = pop_first(question, ("options", "answers", "response_options"))
        choices = build_choices(legacy_choices)
        if choices:
            question["choices"] = choices
            record("constructed choices from legacy options")
    else:
        normalised, did_update = normalise_choices(question["choices"])
        if did_update:
            question["choices"] = normalised
            record("normalised existing choices")

    set_if_missing(question, "answer", question, ("correct_answer", "correct_choice"), record)
    normalise_answer(question, record)

    explanation = question.get("explanation")
    if isinstance(explanation, str):
        question["explanation"] = {"summary": explanation.strip()}
        record("wrapped explanation string into object")
        explanation = question["explanation"]
    elif explanation is None:
        legacy_summary = pop_first(
            question,
            (
                "explanation_text",
                "explanation_summary",
                "rationale",
                "rationale_text",
            ),
        )
        if isinstance(legacy_summary, str) and legacy_summary.strip():
            question["explanation"] = {"summary": legacy_summary.strip()}
            record("created explanation from legacy summary")
            explanation = question["explanation"]

    if isinstance(explanation, dict):
        rationales = explanation.get("rationales")
        if rationales is None:
            legacy_rationales = pop_first(
                question,
                ("rationales", "answer_explanations", "choice_explanations"),
            )
            parsed = build_rationales(legacy_rationales, question.get("choices"))
            if parsed:
                explanation["rationales"] = parsed
                record("constructed rationales from legacy data")
        else:
            parsed, did_update = normalise_rationales(rationales)
            if did_update:
                explanation["rationales"] = parsed
                record("normalised rationales")

    # --- Metadata ------------------------------------------------------------
    metadata = question.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        question["metadata"] = metadata
        record("initialised metadata block")

    metadata_updated, metadata_ops = migrate_metadata(metadata, question)
    if metadata_updated:
        record("; ".join(metadata_ops))

    tags, tags_changed = normalise_tags(question.get("tags"), question)
    if tags_changed:
        question["tags"] = tags
        record("normalised tags")

    # --- Remove deprecated attributes ---------------------------------------
    removed = remove_deprecated_attributes(question)
    if removed:
        record(f"removed deprecated attribute(s): {', '.join(sorted(removed))}")

    return changed, operations


def set_if_missing(
    target: dict,
    dest_key: str,
    source: dict,
    candidate_keys: Sequence[str],
    recorder: Callable[[str], None],
) -> None:
    if dest_key in target:
        return

    value = pop_first(source, candidate_keys)
    if value is None:
        return

    target[dest_key] = value
    recorder(f"set {dest_key} from legacy field")


def pop_first(container: dict, keys: Sequence[str]) -> object | None:
    for key in keys:
        if key in container:
            return container.pop(key)
    return None


def build_choices(raw: object) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []

    choices: list[dict[str, str]] = []
    seen_labels: set[str] = set()

    for index, item in enumerate(raw):
        label = ascii_uppercase[index] if index < len(ascii_uppercase) else str(index + 1)
        text: str | None = None

        if isinstance(item, dict):
            text = to_string(item.get("text") or item.get("value") or item.get("option"))
            if "label" in item and to_string(item["label"]):
                label = str(item["label"]).strip().upper()
            elif "key" in item and to_string(item["key"]):
                label = str(item["key"]).strip().upper()
        elif isinstance(item, str):
            text = item.strip()

        if not text:
            continue

        if label in seen_labels:
            # ensure unique labels by falling back to an ordinal suffix
            ordinal = index + 1
            while f"{label}{ordinal}" in seen_labels:
                ordinal += 1
            label = f"{label}{ordinal}"

        seen_labels.add(label)
        choices.append({"label": label, "text": text})

    return choices


def normalise_choices(raw: object) -> tuple[list[dict[str, str]], bool]:
    if not isinstance(raw, list):
        return [], True

    choices: list[dict[str, str]] = []
    changed = False
    seen_labels: set[str] = set()

    for index, choice in enumerate(raw):
        label = ascii_uppercase[index] if index < len(ascii_uppercase) else str(index + 1)
        text = None
        if isinstance(choice, dict):
            if "label" in choice and isinstance(choice["label"], str):
                candidate = choice["label"].strip().upper()
                if candidate:
                    label = candidate
                if candidate != choice["label"]:
                    changed = True
            if "text" in choice and isinstance(choice["text"], str):
                text = choice["text"].strip()
                if text != choice["text"]:
                    changed = True
        elif isinstance(choice, str):
            text = choice.strip()
            changed = True
        else:
            changed = True

        if not text:
            continue

        if label in seen_labels:
            changed = True
            ordinal = index + 1
            while f"{label}{ordinal}" in seen_labels:
                ordinal += 1
            label = f"{label}{ordinal}"

        seen_labels.add(label)
        choices.append({"label": label, "text": text})

    return choices, changed


def normalise_answer(question: dict, recorder) -> None:
    answer = question.get("answer")
    if answer is None:
        return

    choices = question.get("choices")
    labels = []
    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict) and isinstance(choice.get("label"), str):
                labels.append(choice["label"])

    if isinstance(answer, str):
        candidate = answer.strip()
        if not candidate:
            return
        if candidate.upper() in labels:
            if candidate != candidate.upper():
                question["answer"] = candidate.upper()
                recorder("upper-cased answer label")
            return
        if labels:
            for label, choice in zip(labels, choices or []):
                if isinstance(choice, dict):
                    text = choice.get("text")
                    if isinstance(text, str) and text.strip().lower() == candidate.lower():
                        question["answer"] = label
                        recorder("mapped answer text to label")
                        return
    elif isinstance(answer, int) and labels:
        index = answer
        if 0 <= index < len(labels):
            question["answer"] = labels[index]
            recorder("converted numeric answer to label")
            return


def build_rationales(raw: object, choices: object) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []

    labels = []
    if isinstance(choices, list):
        for choice in choices:
            if isinstance(choice, dict) and isinstance(choice.get("label"), str):
                labels.append(choice["label"])

    rationales: list[dict[str, str]] = []

    for index, item in enumerate(raw):
        label = labels[index] if index < len(labels) else None
        text = None
        if isinstance(item, dict):
            text = to_string(item.get("text") or item.get("rationale"))
            if "choice" in item and to_string(item["choice"]):
                label = str(item["choice"]).strip().upper()
        elif isinstance(item, str):
            text = item.strip()

        if not text:
            continue

        if not label:
            label = ascii_uppercase[index] if index < len(ascii_uppercase) else str(index + 1)

        rationales.append({"choice": label, "text": text})

    return rationales


def normalise_rationales(raw: object) -> tuple[list[dict[str, str]], bool]:
    if not isinstance(raw, list):
        return [], True

    rationales: list[dict[str, str]] = []
    changed = False

    for index, rationale in enumerate(raw):
        label = ascii_uppercase[index] if index < len(ascii_uppercase) else str(index + 1)
        text = None
        if isinstance(rationale, dict):
            if "choice" in rationale and isinstance(rationale["choice"], str):
                candidate = rationale["choice"].strip().upper()
                if candidate:
                    label = candidate
                if candidate != rationale["choice"]:
                    changed = True
            if "text" in rationale and isinstance(rationale["text"], str):
                text = rationale["text"].strip()
                if text != rationale["text"]:
                    changed = True
        elif isinstance(rationale, str):
            text = rationale.strip()
            changed = True
        else:
            changed = True

        if not text:
            continue

        rationales.append({"choice": label, "text": text})

    return rationales, changed


def migrate_metadata(metadata: dict, question: dict) -> tuple[bool, List[str]]:
    changed = False
    operations: List[str] = []

    def set_field(key: str, value: str) -> None:
        nonlocal changed
        metadata[key] = value
        changed = True
        operations.append(f"set metadata.{key}")

    # Legacy keys on the question root may contain metadata values.
    for key, field in (
        ("subject", "subject"),
        ("system", "system"),
        ("difficulty", "difficulty"),
        ("status", "status"),
        ("keywords", "keywords"),
    ):
        if field not in metadata and key in question and not key == "keywords":
            metadata[field] = question.pop(key)
        elif field == "keywords" and "keywords" in question and "keywords" not in metadata:
            metadata["keywords"] = question.pop("keywords")

    subject = normalise_enum(metadata.get("subject"), SUBJECT_CHOICES, SUBJECT_SYNONYMS, "Pathology")
    if metadata.get("subject") != subject:
        set_field("subject", subject)

    system = normalise_enum(metadata.get("system"), SYSTEM_CHOICES, SYSTEM_SYNONYMS, "Multisystem")
    if metadata.get("system") != system:
        set_field("system", system)

    difficulty = normalise_enum(
        metadata.get("difficulty"), DIFFICULTY_CHOICES, DIFFICULTY_SYNONYMS, "Medium"
    )
    if metadata.get("difficulty") != difficulty:
        set_field("difficulty", difficulty)

    status = normalise_enum(metadata.get("status"), STATUS_CHOICES, STATUS_SYNONYMS, "Unused")
    if metadata.get("status") != status:
        set_field("status", status)

    keywords = metadata.get("keywords")
    normalised_keywords = normalise_keywords(keywords, question)
    if metadata.get("keywords") != normalised_keywords:
        metadata["keywords"] = normalised_keywords
        changed = True
        operations.append("normalised metadata.keywords")

    # Optional metadata normalisation for media & references
    media = metadata.get("media")
    media_normalised, media_changed = normalise_media(media, question.get("stem"))
    if media_changed:
        metadata["media"] = media_normalised
        changed = True
        operations.append("normalised metadata.media")

    references = metadata.get("references")
    references_normalised, references_changed = normalise_references(references)
    if references_changed:
        metadata["references"] = references_normalised
        changed = True
        operations.append("normalised metadata.references")

    return changed, operations


def normalise_enum(
    value: object,
    choices: Iterable[str],
    synonyms: dict[str, str],
    default: str,
) -> str:
    if isinstance(value, str):
        normalised = value.strip()
        if not normalised:
            return default

        key = normalised.lower()
        if key in synonyms:
            return synonyms[key]

        for choice in choices:
            if key == choice.lower():
                return choice
            if re.sub(r"[^a-z]", "", key) == re.sub(r"[^a-z]", "", choice.lower()):
                return choice

    return default


def normalise_keywords(raw: object, question: dict) -> list[str]:
    if isinstance(raw, list):
        keywords: list[str] = []
        for entry in raw:
            if isinstance(entry, str):
                cleaned = entry.strip()
                if cleaned:
                    keywords.append(cleaned)
        if keywords:
            return keywords
    elif isinstance(raw, str):
        keywords = [segment.strip() for segment in raw.split(",") if segment.strip()]
        if keywords:
            return keywords

    stem = question.get("stem")
    generated = generate_keywords(stem, question.get("metadata", {}))
    return generated or ["general"]


def generate_keywords(stem: object, metadata: dict) -> list[str]:
    if not isinstance(stem, str):
        stem = ""

    tokens = re.findall(r"[A-Za-z][A-Za-z/-]+", stem.lower())
    seen: set[str] = set()
    keywords: list[str] = []

    for token in tokens:
        if token in STOP_WORDS or len(token) < 4:
            continue
        if token not in seen:
            keywords.append(token)
            seen.add(token)
        if len(keywords) >= 5:
            break

    subject = metadata.get("subject")
    if isinstance(subject, str):
        slug = subject.lower().replace("/", " ")
        for part in slug.split():
            if part and part not in seen:
                keywords.append(part)
                seen.add(part)

    system = metadata.get("system")
    if isinstance(system, str):
        slug = system.lower().replace("/", " ")
        for part in slug.split():
            if part and part not in seen:
                keywords.append(part)
                seen.add(part)

    return keywords[:5]


def normalise_tags(raw: object, question: dict) -> tuple[list[str], bool]:
    tags: list[str] = []
    changed = False

    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, str) and entry.strip():
                cleaned = entry.strip()
                if cleaned not in tags:
                    tags.append(cleaned)
        if len(tags) != len(raw):
            changed = True
    elif isinstance(raw, str) and raw.strip():
        tags = [raw.strip()]
        changed = True
    elif raw not in (None, [], {}):
        changed = True

    derived = derive_tags(question)
    for tag in derived:
        if tag not in tags:
            tags.append(tag)
            changed = True

    if not tags:
        tags = ["general"]
        changed = True

    return tags, changed


def derive_tags(question: dict) -> list[str]:
    tags: list[str] = []
    metadata = question.get("metadata")
    if isinstance(metadata, dict):
        for key in ("subject", "system", "difficulty", "status"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                cleaned = value.strip()
                if cleaned not in tags:
                    tags.append(cleaned)
        keywords = metadata.get("keywords")
        if isinstance(keywords, list):
            for entry in keywords:
                if isinstance(entry, str) and entry.strip():
                    cleaned = entry.strip()
                    if cleaned not in tags:
                        tags.append(cleaned)

    stem = question.get("stem")
    if isinstance(stem, str):
        for token in re.findall(r"[A-Za-z][A-Za-z/-]+", stem.lower()):
            if token in STOP_WORDS or len(token) < 5:
                continue
            candidate = token.strip()
            if candidate and candidate not in tags:
                tags.append(candidate)
            if len(tags) >= 10:
                break

    return tags[:10]


def normalise_media(raw: object, stem: object) -> tuple[list[dict[str, str]], bool]:
    if not isinstance(raw, list):
        return [], bool(raw)

    media: list[dict[str, str]] = []
    changed = False

    fallback_alt = None
    if isinstance(stem, str) and stem:
        fallback_alt = stem.strip()[:120]

    for item in raw:
        if not isinstance(item, dict):
            changed = True
            continue

        entry: dict[str, str] = {}
        media_type = item.get("type") or item.get("media_type")
        if isinstance(media_type, str):
            cleaned_type = media_type.strip().lower()
            if cleaned_type in {"image", "audio", "video"}:
                entry["type"] = cleaned_type
            else:
                cleaned_type = re.sub(r"[^a-z]", "", cleaned_type)
                if cleaned_type in {"image", "audio", "video"}:
                    entry["type"] = cleaned_type
        if "type" not in entry:
            entry["type"] = "image"
            changed = True

        uri = item.get("uri") or item.get("url")
        if isinstance(uri, str) and uri.strip():
            entry["uri"] = uri.strip()
        else:
            continue

        alt_text = item.get("alt_text") or item.get("caption") or fallback_alt
        if isinstance(alt_text, str) and alt_text.strip():
            entry["alt_text"] = alt_text.strip()
        elif fallback_alt:
            entry["alt_text"] = fallback_alt
            changed = True
        else:
            continue

        if entry != item:
            changed = True

        media.append(entry)

    return media, changed


def normalise_references(raw: object) -> tuple[list[dict[str, str]], bool]:
    if not isinstance(raw, list):
        return [], bool(raw)

    references: list[dict[str, str]] = []
    changed = False

    for item in raw:
        if not isinstance(item, dict):
            changed = True
            continue

        title = to_string(item.get("title") or item.get("name"))
        source = to_string(item.get("source") or item.get("publisher"))
        url = to_string(item.get("url") or item.get("link"))

        if not title or not source or not url:
            changed = True
            continue

        reference = {"title": title, "source": source, "url": url}
        if reference != item:
            changed = True

        references.append(reference)

    return references, changed


def remove_deprecated_attributes(question: dict) -> List[str]:
    removed: List[str] = []

    for key in list(question.keys()):
        if key in DEPRECATED_FIELDS or key.startswith(DEPRECATED_PREFIXES):
            question.pop(key, None)
            removed.append(key)

    metadata = question.get("metadata")
    if isinstance(metadata, dict):
        for key in list(metadata.keys()):
            if key in DEPRECATED_FIELDS or key.startswith(DEPRECATED_PREFIXES):
                metadata.pop(key, None)
                removed.append(f"metadata.{key}")

    return removed


def to_string(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    source_path = args.source or Path("data/questions")
    output_dir: Path = args.output_dir

    if not source_path.exists():
        print(f"Error: {source_path} does not exist", file=sys.stderr)
        return 2

    try:
        sources = list(iter_legacy_sources(source_path))
    except ValueError as exc:  # pragma: no cover - runtime guard
        print(exc, file=sys.stderr)
        return 2

    if not sources:
        if source_path.is_file():
            print(f"Error: {source_path} is not a supported JSON/JSONL export", file=sys.stderr)
        else:
            print(f"Error: No JSON files found under {source_path}", file=sys.stderr)
        return 2

    writer = QuestionShardWriter(output_dir, args.shard_size, dry_run=args.dry_run)

    total_questions = 0
    changed_questions = 0
    skipped_entries = 0
    operation_counts: Counter[str] = Counter()

    for source in sources:
        try:
            for question in iter_questions_from_file(source):
                total_questions += 1
                if not isinstance(question, dict):
                    skipped_entries += 1
                    continue

                changed, operations = migrate_question(question)
                if changed:
                    changed_questions += 1
                    operation_counts.update(operations)

                writer.add(question)
        except ValueError as exc:  # pragma: no cover - runtime guard
            print(exc, file=sys.stderr)
            return 2

    emitted_paths = writer.finalize()

    if not total_questions:
        print(f"No question records found in {source_path}", file=sys.stderr)
        return 2

    action = "would write" if args.dry_run else "wrote"
    shard_phrase = f"{len(emitted_paths)} shard(s)" if emitted_paths else "no shards"
    print(
        f"Processed {total_questions} question(s) from {len(sources)} source file(s); "
        f"{action} {shard_phrase} to {output_dir}."
    )
    if skipped_entries:
        print(f"Skipped {skipped_entries} non-dict entr{'y' if skipped_entries == 1 else 'ies'}.")
    if changed_questions:
        print(f"Normalised {changed_questions} question(s).")
    if operation_counts:
        print("Most common normalisation steps:")
        for operation, count in operation_counts.most_common(10):
            print(f" - {operation}: {count}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    sys.exit(main())
