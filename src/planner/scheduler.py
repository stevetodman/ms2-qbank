"""Core scheduling logic for generating structured study plans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Sequence
from uuid import uuid4


@dataclass(frozen=True)
class SubjectPriority:
    """Represents a learner subject focus and its relative weight."""

    subject: str
    priority: int


@dataclass(frozen=True)
class StudyPlanTask:
    """A scheduled block of study time for a subject on a specific day."""

    date: date
    subject: str
    minutes: int


@dataclass(frozen=True)
class StudyPlan:
    """Full study plan timeline returned by the scheduler."""

    plan_id: str
    created_at: datetime
    start_date: date
    exam_date: date
    daily_minutes: int
    tasks: Sequence[StudyPlanTask]


@dataclass(frozen=True)
class StudyPlanParameters:
    """Inputs required to generate a study plan."""

    start_date: date
    exam_date: date
    daily_minutes: int
    subject_priorities: Sequence[SubjectPriority]


class StudyPlanScheduler:
    """Generate a daily schedule that honours subject weights and study capacity."""

    def schedule(self, params: StudyPlanParameters) -> StudyPlan:
        if params.exam_date <= params.start_date:
            raise ValueError("exam_date must be after start_date")
        if params.daily_minutes <= 0:
            raise ValueError("daily study minutes must be positive")
        if not params.subject_priorities:
            raise ValueError("at least one subject priority is required")

        subjects: list[SubjectPriority] = []
        for item in params.subject_priorities:
            subject = item.subject.strip()
            if not subject:
                raise ValueError("subjects must not be empty")
            if item.priority <= 0:
                raise ValueError("subject priorities must be positive integers")
            subjects.append(SubjectPriority(subject=subject, priority=int(item.priority)))

        total_days = (params.exam_date - params.start_date).days
        if total_days <= 0:
            raise ValueError("no study days available before the exam date")

        day_list = [params.start_date + timedelta(days=offset) for offset in range(total_days)]
        total_minutes = params.daily_minutes * total_days
        total_priority = sum(item.priority for item in subjects)

        allocations = self._allocate_minutes(subjects, total_minutes, total_priority)
        tasks = self._distribute_minutes(day_list, params.daily_minutes, allocations)

        return StudyPlan(
            plan_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            start_date=params.start_date,
            exam_date=params.exam_date,
            daily_minutes=params.daily_minutes,
            tasks=tuple(tasks),
        )

    @staticmethod
    def _allocate_minutes(
        subjects: Sequence[SubjectPriority], total_minutes: int, total_priority: int
    ) -> list[tuple[str, int]]:
        if total_minutes <= 0:
            raise ValueError("total study minutes must be positive")
        if total_priority <= 0:
            raise ValueError("total priority weight must be positive")

        remaining = total_minutes
        allocations: list[tuple[str, int]] = []
        for index, item in enumerate(sorted(subjects, key=lambda p: p.priority, reverse=True)):
            if index == len(subjects) - 1:
                minutes = remaining
            else:
                proportional = (total_minutes * item.priority) / total_priority
                minutes = max(1, int(round(proportional)))
                if minutes > remaining:
                    minutes = remaining
            allocations.append((item.subject, minutes))
            remaining -= minutes

        # Guard against rounding issues leaving spare minutes.
        if remaining > 0 and allocations:
            subject, minutes = allocations[-1]
            allocations[-1] = (subject, minutes + remaining)
        elif remaining < 0:
            # Adjust for potential over-allocation due to rounding.
            subject, minutes = allocations[-1]
            allocations[-1] = (subject, minutes + remaining)

        return allocations

    @staticmethod
    def _distribute_minutes(
        days: Sequence[date], daily_minutes: int, allocations: Iterable[tuple[str, int]]
    ) -> list[StudyPlanTask]:
        tasks: list[StudyPlanTask] = []
        day_capacity = [daily_minutes for _ in days]
        day_index = 0

        for subject, minutes in allocations:
            remaining = minutes
            while remaining > 0:
                if day_index >= len(days):
                    raise ValueError("Not enough calendar capacity to schedule all minutes")
                capacity = day_capacity[day_index]
                if capacity <= 0:
                    day_index += 1
                    continue

                chunk = min(capacity, remaining)
                tasks.append(
                    StudyPlanTask(
                        date=days[day_index],
                        subject=subject,
                        minutes=chunk,
                    )
                )
                day_capacity[day_index] -= chunk
                remaining -= chunk

                if day_capacity[day_index] <= 0:
                    day_index += 1

        return tasks


__all__ = [
    "SubjectPriority",
    "StudyPlanTask",
    "StudyPlan",
    "StudyPlanParameters",
    "StudyPlanScheduler",
]
