"""Utility to migrate review events from JSON to SQLite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviews import ReviewStore
from reviews.models import ReviewRecord


def migrate(source: Path, destination: Path) -> int:
    data = json.loads(source.read_text(encoding="utf-8"))
    questions = data.get("questions", {})

    store = ReviewStore(destination)

    migrated = 0
    for question_id, payload in questions.items():
        record = ReviewRecord.from_dict(payload)
        for event in record.events:
            store.append(question_id, event)
        migrated += 1
    return migrated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the legacy JSON file")
    parser.add_argument("destination", type=Path, help="Path to the SQLite database to create")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove the destination file if it already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"Source file {args.source} does not exist")

    if args.destination.exists():
        if args.overwrite:
            args.destination.unlink()
        else:
            raise SystemExit(
                f"Destination {args.destination} already exists. Use --overwrite to replace it."
            )

    migrated = migrate(args.source, args.destination)
    print(f"Migrated {migrated} question review histories to {args.destination}")


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
