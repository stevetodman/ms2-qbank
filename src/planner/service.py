"""High level study planner orchestration helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable

from .models import (
    StudyPlanCreateRequest,
    StudyPlanModel,
    StudyPlanSubjectBreakdown,
    StudyPlanTaskModel,
)
from .scheduler import StudyPlan, StudyPlanParameters, StudyPlanScheduler, StudyPlanTask, SubjectPriority


class StudyPlannerService:
    """Handle lifecycle operations for study plans."""

    def __init__(self, scheduler: StudyPlanScheduler | None = None) -> None:
        self.scheduler = scheduler or StudyPlanScheduler()
        self._plans: dict[str, StudyPlan] = {}

    def create_plan(self, payload: StudyPlanCreateRequest) -> StudyPlanModel:
        start_date = payload.start_date or date.today()
        daily_minutes = int(round(payload.daily_study_hours * 60))
        if daily_minutes <= 0:
            raise ValueError("daily_study_hours resolves to zero minutes")

        params = StudyPlanParameters(
            start_date=start_date,
            exam_date=payload.exam_date,
            daily_minutes=daily_minutes,
            subject_priorities=[
                SubjectPriority(subject=item.subject, priority=item.priority)
                for item in payload.subject_priorities
            ],
        )
        plan = self.scheduler.schedule(params)
        self._plans[plan.plan_id] = plan
        return self._to_response(plan)

    def list_plans(self) -> list[StudyPlanModel]:
        plans = sorted(self._plans.values(), key=lambda plan: plan.created_at, reverse=True)
        return [self._to_response(plan) for plan in plans]

    def get_plan(self, plan_id: str) -> StudyPlanModel:
        if plan_id not in self._plans:
            raise KeyError(plan_id)
        return self._to_response(self._plans[plan_id])

    def delete_plan(self, plan_id: str) -> None:
        if plan_id not in self._plans:
            raise KeyError(plan_id)
        del self._plans[plan_id]

    def _to_response(self, plan: StudyPlan) -> StudyPlanModel:
        start_date = plan.start_date
        exam_date = plan.exam_date
        tasks = list(plan.tasks)
        daily_minutes = plan.daily_minutes

        return StudyPlanModel(
            plan_id=plan.plan_id,
            created_at=plan.created_at,
            start_date=start_date,
            exam_date=exam_date,
            days=(exam_date - start_date).days,
            daily_study_hours=round(daily_minutes / 60, 2),
            total_study_hours=round(sum(task.minutes for task in tasks) / 60, 2),
            tasks=[self._convert_task(task) for task in tasks],
            subject_breakdown=self._aggregate_subjects(tasks),
        )

    @staticmethod
    def _convert_task(task: StudyPlanTask) -> StudyPlanTaskModel:
        return StudyPlanTaskModel(
            date=task.date,
            subject=task.subject,
            hours=round(task.minutes / 60, 2),
        )

    @staticmethod
    def _aggregate_subjects(tasks: Iterable[StudyPlanTask]) -> list[StudyPlanSubjectBreakdown]:
        totals: dict[str, int] = defaultdict(int)
        total_minutes = 0
        for task in tasks:
            totals[task.subject] += task.minutes
            total_minutes += task.minutes

        breakdown: list[StudyPlanSubjectBreakdown] = []
        for subject, minutes in sorted(totals.items(), key=lambda item: item[1], reverse=True):
            hours = round(minutes / 60, 2)
            percentage = round((minutes / total_minutes) * 100 if total_minutes else 0, 1)
            breakdown.append(
                StudyPlanSubjectBreakdown(
                    subject=subject,
                    allocated_hours=hours,
                    percentage=percentage,
                )
            )
        return breakdown


__all__ = ["StudyPlannerService"]
