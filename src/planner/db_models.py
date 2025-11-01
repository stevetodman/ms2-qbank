"""Database models for study plan persistence."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Column, DateTime, Field as SQLField, SQLModel


class StudyPlanDB(SQLModel, table=True):
    """Database model for study plans."""

    __tablename__ = "study_plans"

    # Primary key
    plan_id: str = SQLField(primary_key=True)

    # User association (FK will be added when databases are unified)
    user_id: Optional[int] = SQLField(default=None, index=True)

    # Plan metadata
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    start_date: date = SQLField()
    exam_date: date = SQLField()
    daily_minutes: int = SQLField()


class StudyPlanTaskDB(SQLModel, table=True):
    """Database model for individual study plan tasks."""

    __tablename__ = "study_plan_tasks"

    # Primary key
    id: Optional[int] = SQLField(default=None, primary_key=True)

    # Foreign key to study plan
    plan_id: str = SQLField(foreign_key="study_plans.plan_id", index=True)

    # Task details
    task_date: date = SQLField()
    subject: str = SQLField(max_length=255)
    minutes: int = SQLField()


__all__ = ["StudyPlanDB", "StudyPlanTaskDB"]
