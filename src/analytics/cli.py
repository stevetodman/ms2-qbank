"""Command line helpers for generating analytics reports."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .reporting import (
    compute_metrics_from_directory,
    render_markdown,
    write_if_changed,
    write_json_if_changed,
)

DEFAULT_DATA_DIR = Path("data/questions")
DEFAULT_ARTIFACT_DIR = Path("data/analytics")
DEFAULT_DOCS_MARKDOWN = Path("docs/analysis/question-metrics.md")
DEFAULT_DOCS_JSON = Path("docs/analysis/question-metrics.json")


def _ensure_utc(now: Optional[datetime] = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _format_timestamp(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def _serialise_payload(metrics: Mapping[str, object], generated_at: datetime) -> str:
    payload = {
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "metrics": metrics,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def run_generation_cycle(
    data_dir: Path,
    artifact_dir: Path,
    docs_markdown: Optional[Path] = None,
    docs_json: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Mapping[str, object]:
    """Generate analytics artifacts once and return a summary."""

    timestamp = _ensure_utc(now)
    metrics = compute_metrics_from_directory(data_dir)
    metrics_dict = metrics.to_dict()
    markdown = render_markdown(metrics)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    formatted_timestamp = _format_timestamp(timestamp)

    markdown_path = artifact_dir / f"{formatted_timestamp}.md"
    json_path = artifact_dir / f"{formatted_timestamp}.json"

    markdown_path.write_text(f"{markdown}\n", encoding="utf-8")
    json_path.write_text(f"{_serialise_payload(metrics_dict, timestamp)}\n", encoding="utf-8")

    if docs_markdown is not None:
        write_if_changed(docs_markdown, markdown)
    if docs_json is not None:
        write_json_if_changed(docs_json, metrics_dict)

    return {
        "timestamp": formatted_timestamp,
        "generated_at": timestamp.isoformat().replace("+00:00", "Z"),
        "markdown_path": markdown_path,
        "json_path": json_path,
        "metrics": metrics_dict,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate analytics metrics on a schedule.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--docs-markdown", type=Path, default=DEFAULT_DOCS_MARKDOWN)
    parser.add_argument("--docs-json", type=Path, default=DEFAULT_DOCS_JSON)
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Optional interval in seconds for continuous generation. 0 disables scheduling.",
    )
    parser.add_argument(
        "--skip-docs",
        action="store_true",
        help="Do not update the markdown and JSON documentation outputs.",
    )
    return parser


def _run_once(args: argparse.Namespace) -> Mapping[str, object]:
    docs_markdown: Optional[Path] = None if args.skip_docs else args.docs_markdown
    docs_json: Optional[Path] = None if args.skip_docs else args.docs_json
    return run_generation_cycle(
        data_dir=args.data_dir,
        artifact_dir=args.artifact_dir,
        docs_markdown=docs_markdown,
        docs_json=docs_json,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = _run_once(args)
        print(
            f"Generated analytics at {result['generated_at']} → {result['json_path'].as_posix()}",
            file=sys.stdout,
        )

        interval = args.interval
        while interval and interval > 0:
            time.sleep(interval)
            result = _run_once(args)
            print(
                f"Generated analytics at {result['generated_at']} → {result['json_path'].as_posix()}",
                file=sys.stdout,
            )
    except KeyboardInterrupt:
        print("Analytics generation interrupted", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
