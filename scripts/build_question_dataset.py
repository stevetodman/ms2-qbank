#!/usr/bin/env python3
"""Normalise legacy question exports into production-ready dataset shards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from questions.pipeline import BuildResult, DatasetBuildError, build_question_dataset


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help="Legacy export files or directories containing JSON question payloads.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/questions/production"),
        help="Directory where normalised dataset chunks will be written.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum number of questions per generated JSON file.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("data/schema/question.schema.json"),
        help="Path to the JSON schema used for validation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the migration without writing any files.",
    )
    parser.add_argument(
        "--no-validate",
        dest="validate",
        action="store_false",
        help="Skip schema validation of the generated dataset.",
    )
    parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Do not remove existing JSON files in the output directory before writing.",
    )
    parser.add_argument(
        "--keep-on-validation-error",
        dest="raise_on_validation_error",
        action="store_false",
        help="Return successfully even if validation reports errors.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed per-record migration notes.",
    )
    return parser.parse_args(argv)


def _print_summary(result: BuildResult, *, verbose: bool = False) -> None:
    print(
        f"Processed {result.processed_records} question(s) from {len(result.input_files)} input file(s).",
        file=sys.stdout,
    )
    if result.skipped_records:
        print(f"Skipped {result.skipped_records} record(s) that were not question objects.")
    print(f"Prepared {result.migrated_records} question(s). Dry run: {result.dry_run}.")

    if result.output_files:
        print("Output files:")
        for path in result.output_files:
            suffix = " (planned)" if result.dry_run else ""
            print(f" - {path}{suffix}")

    if result.validated_records:
        print(f"Validated {result.validated_records} question(s) against the schema.")

    if verbose and result.notes:
        print("\nDetailed notes:")
        for note in result.notes:
            print(f" - {note}")

    if result.validation_errors:
        print("\nValidation errors:", file=sys.stderr)
        for path, errors in sorted(result.validation_errors.items()):
            print(f" - {path}: {len(errors)} error(s)", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = build_question_dataset(
            args.sources,
            output_dir=args.output_dir,
            chunk_size=args.chunk_size,
            dry_run=args.dry_run,
            schema_path=args.schema,
            validate=args.validate,
            clean=args.clean,
            raise_on_validation_error=args.raise_on_validation_error,
        )
    except DatasetBuildError as exc:
        if exc.result is not None:
            _print_summary(exc.result, verbose=args.verbose)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - unexpected runtime failure
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    _print_summary(result, verbose=args.verbose)

    if result.validation_errors:
        return 1 if args.raise_on_validation_error else 0

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
