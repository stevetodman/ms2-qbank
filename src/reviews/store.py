"""Persistence layer for question review records backed by SQLite."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Awaitable, Callable, Iterable, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Session, SQLModel, select
from sqlmodel import create_engine

from .models import ReviewAction, ReviewEvent, ReviewRecord, ReviewerRole


class ReviewEventRow(SQLModel, table=True):
    """ORM representation of :class:`reviews.models.ReviewEvent`."""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: str = Field(index=True, nullable=False)
    reviewer: str = Field(nullable=False)
    role: ReviewerRole = Field(nullable=False)
    action: ReviewAction = Field(nullable=False)
    comment: Optional[str] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    def to_domain(self) -> ReviewEvent:
        return ReviewEvent(
            reviewer=self.reviewer,
            action=self.action,
            role=self.role,
            comment=self.comment,
            timestamp=self.timestamp,
        )

    @classmethod
    def from_domain(cls, question_id: str, event: ReviewEvent) -> "ReviewEventRow":
        return cls(
            question_id=question_id,
            reviewer=event.reviewer,
            role=event.role,
            action=event.action,
            comment=event.comment,
            timestamp=event.timestamp,
        )


StatusHook = Callable[[str, str, str], Optional[Awaitable[None]]]


@dataclass
class _AnalyticsDispatcher:
    hook: Optional[StatusHook] = None

    def emit(self, question_id: str, previous_status: str, new_status: str) -> None:
        if not self.hook or previous_status == new_status:
            return

        result = self.hook(question_id, previous_status, new_status)
        if inspect.isawaitable(result):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                loop.create_task(result)  # type: ignore[arg-type]
            else:
                asyncio.run(result)


class ReviewStore:
    """SQLite-backed review store compatible with the legacy interface."""

    def __init__(self, path: Path | str, analytics_hook: Optional[StatusHook] = None):
        self._path = Path(path)
        self._lock = Lock()
        self._analytics = _AnalyticsDispatcher(analytics_hook)
        self._engine = create_engine(
            self._database_url(),
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        self._initialise()

    def _database_url(self) -> str:
        as_str = str(self._path)
        if as_str.startswith("sqlite://"):
            return as_str
        if as_str == ":memory:":
            return "sqlite:///:memory:"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self._path}"

    def _initialise(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    def _load_events(self, session: Session, question_id: str) -> Iterable[ReviewEventRow]:
        statement = (
            select(ReviewEventRow)
            .where(ReviewEventRow.question_id == question_id)
            .order_by(ReviewEventRow.timestamp, ReviewEventRow.id)
        )
        return session.exec(statement).all()

    def get(self, question_id: str) -> ReviewRecord:
        with Session(self._engine) as session:
            events = [row.to_domain() for row in self._load_events(session, question_id)]
        return ReviewRecord(question_id=question_id, events=list(events))

    def append(self, question_id: str, event: ReviewEvent) -> ReviewRecord:
        with self._lock:
            with Session(self._engine) as session:
                existing_events = [row.to_domain() for row in self._load_events(session, question_id)]
                record = ReviewRecord(question_id=question_id, events=list(existing_events))
                previous_status = record.current_status()
                new_status = record.apply_event(event)

                row = ReviewEventRow.from_domain(question_id, event)
                session.add(row)
                session.commit()

        self._analytics.emit(question_id, previous_status, new_status)
        return record

    def set_analytics_hook(self, hook: Optional[StatusHook]) -> None:
        """Update the analytics hook used for status transitions."""

        self._analytics.hook = hook
