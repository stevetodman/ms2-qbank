"""Utilities for generating and persisting analytics reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping

from .metrics import QuestionMetrics, compute_question_metrics


def load_question_payloads(data_dir: Path) -> List[Mapping[str, object]]:
    """Load question payloads from ``data_dir``.

    The loader accepts either a list of questions or a single question mapping
    per file. Non-mapping entries are ignored to keep the helper permissive for
    tests and ad-hoc datasets.
    """

    payloads: List[Mapping[str, object]] = []
    if not data_dir.exists():
        return payloads

    for path in sorted(data_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            payloads.extend(item for item in data if isinstance(item, Mapping))
        elif isinstance(data, Mapping):
            payloads.append(data)
    return payloads


def compute_metrics_from_directory(data_dir: Path) -> QuestionMetrics:
    """Compute :class:`QuestionMetrics` for payloads stored in ``data_dir``."""

    questions = load_question_payloads(data_dir)
    return compute_question_metrics(questions)


def render_markdown(metrics: QuestionMetrics) -> str:
    """Render ``metrics`` as a markdown dashboard."""

    usage = metrics.usage_summary

    lines = [
        "# Question Metrics Dashboard",
        "",
        "Automated summary of question usage patterns, difficulty mix, and review status distribution.",
        "",
        "## Overview",
        f"- **Total questions:** {metrics.total_questions}",
        f"- **Questions with tracked usage:** {usage.tracked_questions}",
        f"- **Total usage events:** {usage.total_usage}",
        f"- **Average usage per tracked question:** {usage.average_usage:.2f}",
        "",
        "## Difficulty Distribution",
        _render_table(["Difficulty", "Questions"], metrics.difficulty_distribution.items()),
        "",
        "## Review Status Distribution",
        _render_table(["Status", "Questions"], metrics.review_status_distribution.items()),
        "",
        "## Usage Frequency",
    ]

    if usage.tracked_questions:
        lines.extend(
            [
                _render_table(["Deliveries", "Questions"], usage.usage_distribution.items()),
                "",
                f"- **Minimum deliveries:** {usage.minimum_usage}",
                f"- **Maximum deliveries:** {usage.maximum_usage}",
            ]
        )
    else:
        lines.append("No usage telemetry recorded in metadata.")

    lines.append("")
    return "\n".join(lines)


def write_if_changed(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` if it differs from the existing file."""

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_if_changed(path: Path, payload: Mapping[str, object]) -> None:
    """Persist ``payload`` as JSON if the on-disk content differs."""

    content = json.dumps(payload, indent=2, sort_keys=True)
    write_if_changed(path, f"{content}\n")


def _render_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    headers_list = list(headers)
    header_row = " | ".join(headers_list)
    separator = " | ".join(["---"] * len(headers_list))
    rendered_rows = [header_row, separator]
    for row in rows:
        rendered_rows.append(" | ".join(str(value) for value in row))
    return "\n".join(rendered_rows)


__all__ = [
    "compute_metrics_from_directory",
    "load_question_payloads",
    "render_markdown",
    "write_if_changed",
    "write_json_if_changed",
]
