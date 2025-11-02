"""Shared database utilities for SQLite connection hardening.

This module provides helper functions to configure SQLite connections with
production-ready settings including WAL mode, foreign key enforcement, and
proper concurrency handling.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, event
from sqlalchemy.engine import Connection
from sqlmodel import create_engine


def configure_sqlite_pragmas(connection: Connection, _: Any) -> None:
    """Configure SQLite pragmas for production use.

    This function is designed to be used as a SQLAlchemy event listener
    that runs on each new connection. It configures:

    - WAL (Write-Ahead Logging) mode for better concurrency
    - NORMAL synchronous mode (balanced durability/performance)
    - Foreign key constraint enforcement
    - 5-second busy timeout to handle concurrent writes

    Args:
        connection: SQLAlchemy connection object
        _: Connection record (unused)
    """
    cursor = connection.connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA busy_timeout = 5000")  # 5 seconds in milliseconds
    cursor.close()


def create_hardened_sqlite_engine(
    database_url: str,
    echo: bool = False,
    connect_args: dict[str, Any] | None = None,
) -> Engine:
    """Create a SQLite engine with production-hardening pragmas applied.

    This is a drop-in replacement for `create_engine` that automatically
    configures SQLite connections with:
    - WAL mode for concurrent read/write operations
    - Foreign key constraint enforcement
    - Busy timeout to prevent "database is locked" errors
    - NORMAL synchronous mode for balanced durability

    Args:
        database_url: SQLAlchemy database URL (e.g., "sqlite:///data/mydb.db")
        echo: Whether to log SQL statements (default: False)
        connect_args: Additional connection arguments to pass to create_engine

    Returns:
        Configured SQLAlchemy Engine with pragmas applied on each connection

    Example:
        >>> engine = create_hardened_sqlite_engine("sqlite:///data/users.db")
        >>> # All connections from this engine will have pragmas applied
    """
    # Ensure check_same_thread=False for SQLite to allow multi-threaded access
    default_connect_args = {"check_same_thread": False}
    if connect_args:
        default_connect_args.update(connect_args)

    engine = create_engine(
        database_url,
        echo=echo,
        connect_args=default_connect_args,
    )

    # Register the pragma configuration to run on every new connection
    event.listen(engine, "connect", configure_sqlite_pragmas)

    return engine


def run_migrations_for_engine(engine: Engine, migrations_dir: Any) -> None:
    """Run SQL migration files for a given engine.

    Executes all .sql files in the migrations directory in alphabetical order.
    Migrations should be idempotent (safe to run multiple times).

    Args:
        engine: SQLAlchemy engine to run migrations against
        migrations_dir: Path to directory containing .sql migration files

    Example:
        >>> from pathlib import Path
        >>> engine = create_hardened_sqlite_engine("sqlite:///mydb.db")
        >>> run_migrations_for_engine(engine, Path(__file__).parent / "migrations")
    """
    from pathlib import Path

    migrations_path = Path(migrations_dir) if not isinstance(migrations_dir, Path) else migrations_dir

    if not migrations_path.exists():
        return

    migration_files = sorted(migrations_path.glob("*.sql"))

    for migration_file in migration_files:
        sql = migration_file.read_text(encoding="utf-8")
        try:
            with engine.begin() as conn:
                # Execute each statement separately
                for statement in sql.split(";"):
                    statement = statement.strip()
                    if statement and not statement.startswith("--"):
                        conn.exec_driver_sql(statement)
        except Exception:
            # Migrations are idempotent (CREATE INDEX IF NOT EXISTS),
            # so we can safely ignore errors like "index already exists"
            pass


__all__ = [
    "configure_sqlite_pragmas",
    "create_hardened_sqlite_engine",
    "run_migrations_for_engine",
]
