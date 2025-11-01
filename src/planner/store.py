"""Database-backed persistence for study plans."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select

from .db_models import StudyPlanDB, StudyPlanTaskDB
from .scheduler import StudyPlan, StudyPlanTask


class StudyPlanStore:
    """Handle study plan data persistence with SQLite database."""

    def __init__(self, database_url: str = "sqlite:///data/planner.db") -> None:
        """Initialize the study plan store with a database connection.

        Args:
            database_url: SQLAlchemy database URL
        """
        # Ensure data directory exists
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(database_url, echo=False)
        SQLModel.metadata.create_all(self.engine)

    def save_plan(self, plan: StudyPlan, user_id: Optional[int] = None) -> StudyPlanDB:
        """Save a study plan to the database.

        Args:
            plan: Study plan domain object from scheduler
            user_id: Optional user ID to associate with the plan

        Returns:
            Saved database record
        """
        with Session(self.engine) as session:
            # Create plan record
            plan_db = StudyPlanDB(
                plan_id=plan.plan_id,
                user_id=user_id,
                created_at=plan.created_at,
                start_date=plan.start_date,
                exam_date=plan.exam_date,
                daily_minutes=plan.daily_minutes,
            )

            # Create task records
            tasks_db = [
                StudyPlanTaskDB(
                    plan_id=plan.plan_id,
                    task_date=task.date,
                    subject=task.subject,
                    minutes=task.minutes,
                )
                for task in plan.tasks
            ]

            session.add(plan_db)
            session.add_all(tasks_db)
            session.commit()
            session.refresh(plan_db)

            return plan_db

    def get_plan(self, plan_id: str) -> Optional[StudyPlan]:
        """Retrieve a study plan by ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Study plan domain object, or None if not found
        """
        with Session(self.engine) as session:
            plan_db = session.get(StudyPlanDB, plan_id)
            if not plan_db:
                return None

            # Load tasks
            tasks_db = session.exec(
                select(StudyPlanTaskDB)
                .where(StudyPlanTaskDB.plan_id == plan_id)
                .order_by(StudyPlanTaskDB.task_date)
            ).all()

            # Convert to domain objects
            tasks = [
                StudyPlanTask(
                    date=task_db.task_date,
                    subject=task_db.subject,
                    minutes=task_db.minutes,
                )
                for task_db in tasks_db
            ]

            return StudyPlan(
                plan_id=plan_db.plan_id,
                created_at=plan_db.created_at,
                start_date=plan_db.start_date,
                exam_date=plan_db.exam_date,
                daily_minutes=plan_db.daily_minutes,
                tasks=tuple(tasks),
            )

    def list_plans(self, user_id: Optional[int] = None) -> list[StudyPlan]:
        """List all study plans, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter plans

        Returns:
            List of study plan domain objects
        """
        with Session(self.engine) as session:
            query = select(StudyPlanDB).order_by(StudyPlanDB.created_at.desc())

            if user_id is not None:
                query = query.where(StudyPlanDB.user_id == user_id)

            plans_db = session.exec(query).all()

            plans: list[StudyPlan] = []
            for plan_db in plans_db:
                plan = self.get_plan(plan_db.plan_id)
                if plan:
                    plans.append(plan)

            return plans

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a study plan and its tasks.

        Args:
            plan_id: Plan identifier

        Returns:
            True if plan was deleted, False if not found
        """
        with Session(self.engine) as session:
            plan_db = session.get(StudyPlanDB, plan_id)
            if not plan_db:
                return False

            # Delete tasks first (foreign key constraint)
            tasks_db = session.exec(
                select(StudyPlanTaskDB).where(StudyPlanTaskDB.plan_id == plan_id)
            ).all()
            for task_db in tasks_db:
                session.delete(task_db)

            # Delete plan
            session.delete(plan_db)
            session.commit()

            return True


__all__ = ["StudyPlanStore"]
