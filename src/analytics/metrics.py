"""Utilities for aggregating question bank analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional

Difficulty = str
Status = str
UsageCount = int

_DIFFICULTY_ORDER = ("Easy", "Medium", "Hard")
_STATUS_ORDER = ("Unused", "Marked", "Incorrect", "Correct", "Omitted")


def _normalise_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalise_int(value: Any) -> Optional[int]:
    """Best-effort conversion of *value* to an integer."""

    if isinstance(value, bool):  # bool is a subclass of int; skip on purpose
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class UsageSummary:
    """Aggregated usage metrics for a collection of questions."""

    tracked_questions: int
    total_usage: int
    average_usage: float
    minimum_usage: int
    maximum_usage: int
    usage_distribution: MutableMapping[UsageCount, int]

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "tracked_questions": self.tracked_questions,
            "total_usage": self.total_usage,
            "average_usage": self.average_usage,
            "minimum_usage": self.minimum_usage,
            "maximum_usage": self.maximum_usage,
            "usage_distribution": dict(self.usage_distribution),
        }


@dataclass(frozen=True)
class QuestionMetrics:
    """High-level analytics derived from question metadata."""

    total_questions: int
    difficulty_distribution: MutableMapping[Difficulty, int]
    review_status_distribution: MutableMapping[Status, int]
    usage_summary: UsageSummary
    coverage: Iterable["CoverageMetric"]

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "total_questions": self.total_questions,
            "difficulty_distribution": dict(self.difficulty_distribution),
            "review_status_distribution": dict(self.review_status_distribution),
            "usage_summary": self.usage_summary.to_dict(),
            "coverage": [metric.to_dict() for metric in self.coverage],
        }


@dataclass(frozen=True)
class CoverageMetric:
    """Progress indicator describing completion of contributor tasks."""

    label: str
    completed: int
    missing: int

    def to_dict(self) -> MutableMapping[str, Any]:
        total = self.completed + self.missing
        coverage = (self.completed / total) if total else 1.0
        return {
            "label": self.label,
            "completed": self.completed,
            "missing": self.missing,
            "total": total,
            "coverage": coverage,
        }


def _has_summary(question: Mapping[str, Any]) -> bool:
    explanation = question.get("explanation")
    if not isinstance(explanation, Mapping):
        return False
    summary = explanation.get("summary")
    return bool(_normalise_string(summary))


def _has_rationales(question: Mapping[str, Any]) -> bool:
    explanation = question.get("explanation")
    if not isinstance(explanation, Mapping):
        return False
    rationales = explanation.get("rationales")
    if not isinstance(rationales, Iterable):
        return False
    return any(
        isinstance(entry, Mapping)
        and isinstance(entry.get("choice"), str)
        and bool(_normalise_string(entry.get("text")))
        for entry in rationales
    )


def _has_keywords(question: Mapping[str, Any]) -> bool:
    metadata = question.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    keywords = metadata.get("keywords")
    if not isinstance(keywords, Iterable):
        return False
    return any(bool(_normalise_string(keyword)) for keyword in keywords)


def _has_references(question: Mapping[str, Any]) -> bool:
    metadata = question.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    references = metadata.get("references")
    if not isinstance(references, Iterable):
        return False
    return any(
        isinstance(reference, Mapping)
        and bool(_normalise_string(reference.get("title")))
        and bool(_normalise_string(reference.get("source")))
        for reference in references
    )


def _has_media(question: Mapping[str, Any]) -> bool:
    metadata = question.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    media = metadata.get("media")
    if not isinstance(media, Iterable):
        return False
    return any(
        isinstance(asset, Mapping)
        and bool(_normalise_string(asset.get("type")))
        and bool(_normalise_string(asset.get("uri")))
        for asset in media
    )


def _media_has_alt_text(question: Mapping[str, Any]) -> Optional[bool]:
    metadata = question.get("metadata")
    if not isinstance(metadata, Mapping):
        return None

    media = metadata.get("media")
    if not isinstance(media, Iterable):
        return None

    has_assets = False
    for asset in media:
        if not isinstance(asset, Mapping):
            continue
        asset_type = _normalise_string(asset.get("type"))
        asset_uri = _normalise_string(asset.get("uri"))
        if not asset_type or not asset_uri:
            continue
        has_assets = True
        alt_text = _normalise_string(asset.get("alt_text"))
        if not alt_text:
            return False

    if not has_assets:
        return None

    return True


def _has_usage_count(question: Mapping[str, Any]) -> bool:
    metadata = question.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    usage_value = metadata.get("usage_count")
    normalised = _normalise_int(usage_value)
    return normalised is not None and normalised >= 0


def _has_tags(question: Mapping[str, Any]) -> bool:
    tags = question.get("tags")
    if not isinstance(tags, Iterable):
        return False
    return any(bool(_normalise_string(tag)) for tag in tags)


_COVERAGE_DEFINITIONS: tuple[
    tuple[str, Callable[[Mapping[str, Any]], Optional[bool]]],
    ...
] = (
    ("Explanations drafted", _has_summary),
    ("Answer rationales captured", _has_rationales),
    ("Keywords assigned", _has_keywords),
    ("Reference links added", _has_references),
    ("Media attachments added", _has_media),
    ("Media alt text provided", _media_has_alt_text),
    ("Usage tracking configured", _has_usage_count),
    ("Tags applied", _has_tags),
)


def compute_question_metrics(questions: Iterable[Mapping[str, Any]]) -> QuestionMetrics:
    """Compute aggregate analytics for *questions*.

    The input is expected to be an iterable of mappings that follow the
    ``data/schema/question.schema.json`` contract. Only the ``metadata`` block
    is inspected. Missing or malformed values are ignored gracefully.
    """

    difficulty_counter: Counter[Difficulty] = Counter()
    status_counter: Counter[Status] = Counter()
    usage_counter: Counter[UsageCount] = Counter()
    usage_values: list[int] = []
    coverage_tracker: dict[str, dict[str, int]] = {
        label: {"completed": 0, "missing": 0} for label, _ in _COVERAGE_DEFINITIONS
    }

    total_questions = 0

    for question in questions:
        total_questions += 1

        for label, predicate in _COVERAGE_DEFINITIONS:
            bucket = coverage_tracker[label]
            result = predicate(question)
            if result is True:
                bucket["completed"] += 1
            elif result is False:
                bucket["missing"] += 1

        metadata = question.get("metadata")
        if not isinstance(metadata, Mapping):
            continue

        difficulty = metadata.get("difficulty")
        if isinstance(difficulty, str):
            difficulty_counter[difficulty] += 1

        status = metadata.get("status")
        if isinstance(status, str):
            status_counter[status] += 1

        usage_value = metadata.get("usage_count")
        normalised_usage = _normalise_int(usage_value)
        if normalised_usage is not None and normalised_usage >= 0:
            usage_values.append(normalised_usage)
            usage_counter[normalised_usage] += 1

    usage_summary = _build_usage_summary(usage_values, usage_counter)

    ordered_difficulty = _order_counter(difficulty_counter, _DIFFICULTY_ORDER)
    ordered_status = _order_counter(status_counter, _STATUS_ORDER)
    coverage_metrics = [
        CoverageMetric(label=label, completed=bucket["completed"], missing=bucket["missing"])
        for label, bucket in coverage_tracker.items()
    ]

    return QuestionMetrics(
        total_questions=total_questions,
        difficulty_distribution=ordered_difficulty,
        review_status_distribution=ordered_status,
        usage_summary=usage_summary,
        coverage=coverage_metrics,
    )


def _order_counter(counter: Counter[str], order: Iterable[str]) -> MutableMapping[str, int]:
    ordered: dict[str, int] = {}
    for key in order:
        if counter[key]:
            ordered[key] = counter[key]
    for key, value in sorted(counter.items()):
        if key not in ordered:
            ordered[key] = value
    return ordered


def _build_usage_summary(values: list[int], distribution: Counter[int]) -> UsageSummary:
    if not values:
        return UsageSummary(
            tracked_questions=0,
            total_usage=0,
            average_usage=0.0,
            minimum_usage=0,
            maximum_usage=0,
            usage_distribution={},
        )

    total_usage = sum(values)
    average_usage = float(mean(values)) if values else 0.0
    minimum_usage = min(values)
    maximum_usage = max(values)

    ordered_distribution = dict(sorted(distribution.items()))

    return UsageSummary(
        tracked_questions=len(values),
        total_usage=total_usage,
        average_usage=average_usage,
        minimum_usage=minimum_usage,
        maximum_usage=maximum_usage,
        usage_distribution=ordered_distribution,
    )
