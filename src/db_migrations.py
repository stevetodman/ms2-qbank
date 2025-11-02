"""Database migration runner for applying SQL migrations to SQLite databases.

This module provides a simple migration runner that executes SQL files
in order to update database schemas with indices and constraints.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


def run_migrations(db_path: str | Path, migrations_dir: str | Path) -> tuple[int, list[str]]:
    """Run all SQL migration files in a directory against a database.

    Migrations are executed in alphabetical order by filename.
    Each migration file should be idempotent (safe to run multiple times).

    Args:
        db_path: Path to the SQLite database file
        migrations_dir: Directory containing .sql migration files

    Returns:
        Tuple of (number of migrations applied, list of applied migration names)

    Raises:
        FileNotFoundError: If database or migrations directory doesn't exist
        sqlite3.Error: If any migration fails to execute

    Example:
        >>> run_migrations("data/analytics.db", "src/analytics/migrations")
        (3, ['001_add_indices.sql', '002_add_constraints.sql', '003_optimize.sql'])
    """
    db_path = Path(db_path)
    migrations_dir = Path(migrations_dir)

    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    # Find all .sql files and sort them
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        return (0, [])

    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    applied = []
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")

            # Execute the migration
            try:
                conn.executescript(sql)
                conn.commit()
                applied.append(migration_file.name)
                print(f"✓ Applied {migration_file.name}")
            except sqlite3.Error as e:
                print(f"✗ Failed to apply {migration_file.name}: {e}")
                raise

    finally:
        conn.close()

    return (len(applied), applied)


def run_all_service_migrations(data_dir: str | Path = "data") -> dict[str, tuple[int, list[str]]]:
    """Run migrations for all core services.

    Args:
        data_dir: Base directory where database files are stored

    Returns:
        Dictionary mapping service name to (count, migration list) tuple

    Example:
        >>> results = run_all_service_migrations()
        >>> print(f"Analytics: {results['analytics'][0]} migrations applied")
    """
    data_dir = Path(data_dir)
    src_dir = Path(__file__).parent

    services = {
        "analytics": ("analytics.db", "analytics/migrations"),
        "videos": ("videos.db", "videos/migrations"),
        "flashcards": ("flashcards.db", "flashcards/migrations"),
        "assessments": ("assessments.db", "assessments/migrations"),
        "users": ("users.db", "users/migrations"),
        "library": ("library.db", "library/migrations"),
        "planner": ("planner.db", "planner/migrations"),
    }

    results = {}

    for service_name, (db_file, migrations_subdir) in services.items():
        db_path = data_dir / db_file
        migrations_dir = src_dir / migrations_subdir

        if not migrations_dir.exists():
            print(f"⊘ Skipping {service_name}: no migrations directory")
            continue

        print(f"\n=== Migrating {service_name} ===")
        try:
            count, applied = run_migrations(db_path, migrations_dir)
            results[service_name] = (count, applied)
            if count == 0:
                print(f"  No migrations to apply")
        except Exception as e:
            print(f"  Error: {e}")
            results[service_name] = (0, [])

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Run migration for specific database
        db_path = sys.argv[1]
        migrations_dir = sys.argv[2] if len(sys.argv) > 2 else Path(db_path).parent / "migrations"
        run_migrations(db_path, migrations_dir)
    else:
        # Run all migrations
        print("Running all service migrations...")
        results = run_all_service_migrations()
        print(f"\n{'='*50}")
        print("Summary:")
        for service, (count, _) in results.items():
            print(f"  {service}: {count} migrations")
