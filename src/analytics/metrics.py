"""Utilities for aggregating question bank analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Iterable, Mapping, MutableMapping, Optional

Difficulty = str
Status = str
UsageCount = int

_DIFFICULTY_ORDER = ("Easy", "Medium", "Hard")
_STATUS_ORDER = ("Unused", "Marked", "Incorrect", "Correct", "Omitted")


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

    def to_dict(self) -> MutableMapping[str, Any]:
        return {
            "total_questions": self.total_questions,
            "difficulty_distribution": dict(self.difficulty_distribution),
            "review_status_distribution": dict(self.review_status_distribution),
            "usage_summary": self.usage_summary.to_dict(),
        }


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

    total_questions = 0

    for question in questions:
        total_questions += 1
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

    return QuestionMetrics(
        total_questions=total_questions,
        difficulty_distribution=ordered_difficulty,
        review_status_distribution=ordered_status,
        usage_summary=usage_summary,
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
