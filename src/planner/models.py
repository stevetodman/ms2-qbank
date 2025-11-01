"""Pydantic models used by the study planner service."""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from pydantic import BaseModel, Field, field_validator


class SubjectPriorityInput(BaseModel):
    """Learner supplied priority weighting for a subject."""

    subject: str = Field(..., min_length=1, description="Name of the subject focus")
    priority: int = Field(..., gt=0, description="Relative weight for scheduling")

    @field_validator("subject")
    @classmethod
    def _normalise_subject(cls, value: str) -> str:
        subject = value.strip()
        if not subject:
            raise ValueError("subject must not be empty")
        return subject


class StudyPlanCreateRequest(BaseModel):
    """Payload accepted when requesting a new study plan."""

    exam_date: date = Field(..., description="Scheduled exam date")
    daily_study_hours: float = Field(..., gt=0, description="Hours available to study each day")
    subject_priorities: list[SubjectPriorityInput] = Field(..., min_length=1)
    start_date: date | None = Field(default=None, description="Optional start date override")

    @field_validator("subject_priorities")
    @classmethod
    def _ensure_unique_subjects(
        cls, values: Iterable[SubjectPriorityInput]
    ) -> Iterable[SubjectPriorityInput]:
        seen: set[str] = set()
        unique: list[SubjectPriorityInput] = []
        for item in values:
            key = item.subject.casefold()
            if key in seen:
                raise ValueError("duplicate subjects are not allowed")
            seen.add(key)
            unique.append(item)
        return unique


class StudyPlanTaskModel(BaseModel):
    """A single scheduled study block in the returned plan."""

    date: date
    subject: str
    hours: float


class StudyPlanSubjectBreakdown(BaseModel):
    """Total study hours dedicated to a subject across the plan."""

    subject: str
    allocated_hours: float
    percentage: float


class StudyPlanModel(BaseModel):
    """Serialised representation of a generated study plan."""

    plan_id: str
    created_at: datetime
    start_date: date
    exam_date: date
    days: int
    daily_study_hours: float
    total_study_hours: float
    tasks: list[StudyPlanTaskModel]
    subject_breakdown: list[StudyPlanSubjectBreakdown]


__all__ = [
    "SubjectPriorityInput",
    "StudyPlanCreateRequest",
    "StudyPlanTaskModel",
    "StudyPlanSubjectBreakdown",
    "StudyPlanModel",
]
