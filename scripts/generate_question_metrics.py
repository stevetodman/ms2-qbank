#!/usr/bin/env python3
"""Generate analytics dashboards for the question bank."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analytics.reporting import (  # noqa: E402
    compute_metrics_from_directory,
    render_markdown,
    write_if_changed,
    write_json_if_changed,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/questions"))
    parser.add_argument("--output-markdown", type=Path, default=Path("docs/analysis/question-metrics.md"))
    parser.add_argument("--output-json", type=Path, default=Path("docs/analysis/question-metrics.json"))

    args = parser.parse_args()

    metrics = compute_metrics_from_directory(args.data_dir)

    write_if_changed(args.output_markdown, render_markdown(metrics))
    write_json_if_changed(args.output_json, metrics.to_dict())


if __name__ == "__main__":
    main()
