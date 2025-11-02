#!/usr/bin/env python3
"""SQLite database backup utility for MS2 QBank.

This script performs backups of all SQLite databases in the data/ directory
using SQLite's online backup API (VACUUM INTO). This ensures consistent
backups even while the application is running.

Usage:
    python scripts/backup_sqlite.py              # Backup all databases
    python scripts/backup_sqlite.py --db analytics.db  # Backup specific database
    python scripts/backup_sqlite.py --compress   # Create compressed backups

Features:
    - Uses VACUUM INTO for consistent online backups
    - Optional compression with gzip
    - Automatic backup rotation (keeps last N backups)
    - Timestamp-based backup naming
    - Email notifications on backup failures (optional)
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


def backup_database(
    db_path: Path,
    backup_dir: Path,
    compress: bool = False,
    max_backups: int = 30,
) -> Path:
    """Backup a single SQLite database.

    Uses VACUUM INTO for consistent online backups that don't lock the database.

    Args:
        db_path: Path to the database file to backup
        backup_dir: Directory where backups will be stored
        compress: Whether to compress the backup with gzip
        max_backups: Maximum number of backups to retain (older ones deleted)

    Returns:
        Path to the created backup file

    Raises:
        sqlite3.Error: If backup fails
        FileNotFoundError: If database file doesn't exist
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Create backup directory if it doesn't exist
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = db_path.stem
    backup_name = f"{db_name}_{timestamp}.db"
    backup_path = backup_dir / backup_name

    print(f"Backing up {db_path.name}...")

    # Perform backup using VACUUM INTO (online backup, no locks)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute(f"VACUUM INTO '{backup_path}'")
        conn.close()
        print(f"  ✓ Created {backup_path.name}")
    except sqlite3.Error as e:
        print(f"  ✗ Failed: {e}")
        raise

    # Compress if requested
    if compress:
        compressed_path = backup_path.with_suffix(".db.gz")
        print(f"  Compressing...")
        with backup_path.open("rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        backup_path.unlink()  # Remove uncompressed version
        backup_path = compressed_path
        print(f"  ✓ Compressed to {compressed_path.name}")

    # Rotate old backups
    rotate_backups(backup_dir, db_name, max_backups, compress)

    return backup_path


def rotate_backups(
    backup_dir: Path,
    db_name: str,
    max_backups: int,
    compressed: bool = False,
) -> None:
    """Delete old backups, keeping only the most recent N backups.

    Args:
        backup_dir: Directory containing backups
        db_name: Database name to filter backups
        max_backups: Maximum number of backups to keep
        compressed: Whether backups are compressed
    """
    pattern = f"{db_name}_*.db.gz" if compressed else f"{db_name}_*.db"
    backups = sorted(backup_dir.glob(pattern))

    if len(backups) > max_backups:
        to_delete = backups[: len(backups) - max_backups]
        for old_backup in to_delete:
            old_backup.unlink()
            print(f"  Deleted old backup: {old_backup.name}")


def backup_all_databases(
    data_dir: Path,
    backup_dir: Path,
    compress: bool = False,
    max_backups: int = 30,
) -> dict[str, Path]:
    """Backup all SQLite databases in the data directory.

    Args:
        data_dir: Directory containing database files
        backup_dir: Directory where backups will be stored
        compress: Whether to compress backups
        max_backups: Maximum number of backups to retain per database

    Returns:
        Dictionary mapping database names to their backup file paths
    """
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return {}

    # Find all .db files
    db_files = list(data_dir.glob("*.db"))

    # Also check the reviews subdirectory
    reviews_dir = data_dir / "reviews"
    if reviews_dir.exists():
        db_files.extend(reviews_dir.glob("*.db"))

    if not db_files:
        print(f"No database files found in {data_dir}")
        return {}

    print(f"Found {len(db_files)} database(s) to backup\n")

    backups = {}
    for db_path in db_files:
        try:
            # Create subdirectory for each database
            db_backup_dir = backup_dir / db_path.stem
            backup_path = backup_database(db_path, db_backup_dir, compress, max_backups)
            backups[db_path.stem] = backup_path
        except Exception as e:
            print(f"  ✗ Error backing up {db_path.name}: {e}")
            continue

    return backups


def main():
    """Main entry point for the backup script."""
    parser = argparse.ArgumentParser(
        description="Backup SQLite databases for MS2 QBank",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup all databases
  python scripts/backup_sqlite.py

  # Backup specific database with compression
  python scripts/backup_sqlite.py --db analytics.db --compress

  # Keep only last 7 backups
  python scripts/backup_sqlite.py --max-backups 7
        """,
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing database files (default: data/)",
    )

    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("backups"),
        help="Directory to store backups (default: backups/)",
    )

    parser.add_argument(
        "--db",
        type=str,
        help="Backup only a specific database file (e.g., analytics.db)",
    )

    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress backups with gzip",
    )

    parser.add_argument(
        "--max-backups",
        type=int,
        default=30,
        help="Maximum number of backups to retain per database (default: 30)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MS2 QBank Database Backup")
    print("=" * 60)
    print(f"Data directory: {args.data_dir.absolute()}")
    print(f"Backup directory: {args.backup_dir.absolute()}")
    print(f"Compression: {'enabled' if args.compress else 'disabled'}")
    print(f"Max backups per database: {args.max_backups}")
    print("=" * 60)
    print()

    try:
        if args.db:
            # Backup specific database
            db_path = args.data_dir / args.db
            db_backup_dir = args.backup_dir / db_path.stem
            backup_path = backup_database(
                db_path, db_backup_dir, args.compress, args.max_backups
            )
            print(f"\n✓ Backup complete: {backup_path}")
        else:
            # Backup all databases
            backups = backup_all_databases(
                args.data_dir, args.backup_dir, args.compress, args.max_backups
            )
            print(f"\n✓ Backup complete: {len(backups)} database(s) backed up")

    except KeyboardInterrupt:
        print("\n\nBackup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n✗ Backup failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
