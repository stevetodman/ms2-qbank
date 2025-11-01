from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from planner import (
    StudyPlanParameters,
    StudyPlanScheduler,
    SubjectPriority,
    create_app,
)


def test_scheduler_allocates_minutes_based_on_priority() -> None:
    scheduler = StudyPlanScheduler()
    start_date = date(2024, 1, 1)
    exam_date = start_date + timedelta(days=5)
    params = StudyPlanParameters(
        start_date=start_date,
        exam_date=exam_date,
        daily_minutes=180,
        subject_priorities=[
            SubjectPriority(subject="Cardiology", priority=3),
            SubjectPriority(subject="Neurology", priority=1),
        ],
    )

    plan = scheduler.schedule(params)

    assert plan.daily_minutes == 180
    assert plan.start_date == start_date
    assert plan.exam_date == exam_date
    total_minutes = sum(task.minutes for task in plan.tasks)
    assert total_minutes == 180 * 5
    assert all(task.minutes > 0 for task in plan.tasks)

    # Highest priority subject should receive at least half of the minutes.
    cardio_minutes = sum(task.minutes for task in plan.tasks if task.subject == "Cardiology")
    neuro_minutes = sum(task.minutes for task in plan.tasks if task.subject == "Neurology")
    assert cardio_minutes > neuro_minutes

    # Tasks should be ordered by date.
    task_dates = [task.date for task in plan.tasks]
    assert task_dates == sorted(task_dates)


@pytest.fixture()
def planner_client() -> TestClient:
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_planner_api_lifecycle(planner_client: TestClient) -> None:
    payload = {
        "start_date": "2024-06-01",
        "exam_date": "2024-06-10",
        "daily_study_hours": 4,
        "subject_priorities": [
            {"subject": "Microbiology", "priority": 2},
            {"subject": "Biochemistry", "priority": 1},
        ],
    }

    response = planner_client.post("/plans", json=payload)
    assert response.status_code == 201
    created = response.json()
    plan_id = created["plan_id"]
    assert created["daily_study_hours"] == pytest.approx(4.0)
    assert created["days"] == 9
    assert created["subject_breakdown"][0]["subject"] == "Microbiology"

    response = planner_client.get("/plans")
    assert response.status_code == 200
    plans = response.json()
    assert any(plan["plan_id"] == plan_id for plan in plans)

    response = planner_client.get(f"/plans/{plan_id}")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["plan_id"] == plan_id
    assert len(retrieved["tasks"]) > 0

    response = planner_client.delete(f"/plans/{plan_id}")
    assert response.status_code == 204

    response = planner_client.get(f"/plans/{plan_id}")
    assert response.status_code == 404
