#!/usr/bin/env python3
"""Generate analytics dashboards for the question bank."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Mapping

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analytics import QuestionMetrics, compute_question_metrics


def load_question_payloads(data_dir: Path) -> List[Mapping[str, object]]:
    payloads: List[Mapping[str, object]] = []
    for path in sorted(data_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                payloads.extend(item for item in data if isinstance(item, Mapping))
            elif isinstance(data, Mapping):
                payloads.append(data)
    return payloads


def render_markdown(metrics: QuestionMetrics) -> str:
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


def _render_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    headers_list = list(headers)
    header_row = " | ".join(headers_list)
    separator = " | ".join(["---"] * len(headers_list))
    rendered_rows = [header_row, separator]
    for row in rows:
        rendered_rows.append(" | ".join(str(value) for value in row))
    return "\n".join(rendered_rows)


def write_if_changed(path: Path, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_if_changed(path: Path, payload: Mapping[str, object]) -> None:
    content = json.dumps(payload, indent=2, sort_keys=True)
    write_if_changed(path, f"{content}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/questions"))
    parser.add_argument("--output-markdown", type=Path, default=Path("docs/analysis/question-metrics.md"))
    parser.add_argument("--output-json", type=Path, default=Path("docs/analysis/question-metrics.json"))

    args = parser.parse_args()

    questions = load_question_payloads(args.data_dir)
    metrics = compute_question_metrics(questions)

    write_if_changed(args.output_markdown, render_markdown(metrics))
    write_json_if_changed(args.output_json, metrics.to_dict())


if __name__ == "__main__":
    main()
