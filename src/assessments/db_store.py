"""Database-backed assessment store for persistence."""

import json
import uuid
import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Iterable, Mapping
from sqlmodel import Session, SQLModel, create_engine, select

from .db_models import AssessmentDB, AssessmentScoreResponse


class AssessmentDatabaseStore:
    """Database-backed store for assessments."""

    def __init__(self, db_path: str = "assessments.db", question_count: int = 160):
        """Initialize the assessment store with a database connection."""
        if not db_path.startswith("sqlite:///"):
            db_path = f"sqlite:///{db_path}"

        self.engine = create_engine(db_path, echo=False)
        self._question_count = max(1, int(question_count))
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        from .db_models import AssessmentDB
        SQLModel.metadata.create_all(self.engine)

    @property
    def question_count(self) -> int:
        return self._question_count

    def create(
        self,
        candidate_id: str,
        subject: Optional[str] = None,
        system: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: list[str] = None,
        time_limit_minutes: int = 280,
    ) -> AssessmentDB:
        """Create a new assessment."""
        assessment = AssessmentDB(
            assessment_id=uuid.uuid4().hex,
            candidate_id=candidate_id,
            subject=subject,
            system=system,
            difficulty=difficulty,
            tags=json.dumps(tags or []),
            time_limit_minutes=time_limit_minutes,
            status="created",
            created_at=datetime.now(timezone.utc),
            question_ids=json.dumps([]),
            responses=json.dumps({}),
            total_questions=0,
            correct=0,
            incorrect=0,
            omitted=0,
            percentage=0.0,
        )

        with Session(self.engine) as session:
            session.add(assessment)
            session.commit()
            session.refresh(assessment)

        return assessment

    def get(self, assessment_id: str) -> Optional[AssessmentDB]:
        """Retrieve an assessment by ID."""
        with Session(self.engine) as session:
            statement = select(AssessmentDB).where(AssessmentDB.assessment_id == assessment_id)
            return session.exec(statement).first()

    def start(
        self,
        assessment_id: str,
        question_ids: list[str],
    ) -> AssessmentDB:
        """Start an assessment with selected questions."""
        with Session(self.engine) as session:
            statement = select(AssessmentDB).where(AssessmentDB.assessment_id == assessment_id)
            assessment = session.exec(statement).first()

            if not assessment:
                raise KeyError(f"Assessment '{assessment_id}' not found")

            if assessment.status not in {"created", "ready"}:
                raise ValueError("Assessment cannot be started in its current state")

            # Update assessment
            assessment.status = "in-progress"
            assessment.started_at = datetime.now(timezone.utc)
            assessment.question_ids = json.dumps(question_ids)
            assessment.total_questions = len(question_ids)
            assessment.responses = json.dumps({})

            # Calculate expiration
            if assessment.time_limit_minutes > 0:
                duration = timedelta(minutes=assessment.time_limit_minutes)
                assessment.expires_at = assessment.started_at + duration
            else:
                assessment.expires_at = None

            session.add(assessment)
            session.commit()
            session.refresh(assessment)

        return assessment

    def submit(
        self,
        assessment_id: str,
        responses: dict[str, Optional[str]],
        correct_answers: dict[str, str],
    ) -> AssessmentDB:
        """Submit responses and compute score."""
        with Session(self.engine) as session:
            statement = select(AssessmentDB).where(AssessmentDB.assessment_id == assessment_id)
            assessment = session.exec(statement).first()

            if not assessment:
                raise KeyError(f"Assessment '{assessment_id}' not found")

            if assessment.status != "in-progress" or not assessment.started_at:
                raise ValueError("Assessment must be started before submission")

            # Store responses
            assessment.responses = json.dumps(responses)
            assessment.submitted_at = datetime.now(timezone.utc)
            assessment.status = "completed"

            # Compute score
            question_ids = json.loads(assessment.question_ids)
            total = len(question_ids)
            correct = 0
            answered = 0

            for qid in question_ids:
                selected = responses.get(qid)
                correct_answer = correct_answers.get(qid)

                if selected:
                    answered += 1
                    if selected == correct_answer:
                        correct += 1

            incorrect = answered - correct
            omitted = total - answered
            percentage = (correct / total * 100) if total > 0 else 0.0

            # Calculate duration
            if assessment.started_at and assessment.submitted_at:
                # Ensure both are timezone-aware for subtraction
                started = assessment.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)

                duration = assessment.submitted_at - started
                assessment.duration_seconds = int(duration.total_seconds())

            # Update score fields
            assessment.total_questions = total
            assessment.correct = correct
            assessment.incorrect = incorrect
            assessment.omitted = omitted
            assessment.percentage = round(percentage, 2)

            session.add(assessment)
            session.commit()
            session.refresh(assessment)

        return assessment

    def get_by_candidate(
        self,
        candidate_id: str,
        limit: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[AssessmentDB]:
        """Retrieve assessments for a candidate."""
        with Session(self.engine) as session:
            statement = select(AssessmentDB).where(
                AssessmentDB.candidate_id == candidate_id
            )

            if status:
                statement = statement.where(AssessmentDB.status == status)

            statement = statement.order_by(AssessmentDB.created_at.desc())

            if limit:
                statement = statement.limit(limit)

            return list(session.exec(statement).all())

    def get_score(self, assessment_id: str) -> Optional[AssessmentScoreResponse]:
        """Get the score for a completed assessment."""
        assessment = self.get(assessment_id)

        if not assessment or assessment.status != "completed":
            return None

        return AssessmentScoreResponse(
            total_questions=assessment.total_questions,
            correct=assessment.correct,
            incorrect=assessment.incorrect,
            omitted=assessment.omitted,
            percentage=assessment.percentage,
            duration_seconds=assessment.duration_seconds,
        )

    def delete(self, assessment_id: str) -> bool:
        """Delete an assessment."""
        with Session(self.engine) as session:
            statement = select(AssessmentDB).where(AssessmentDB.assessment_id == assessment_id)
            assessment = session.exec(statement).first()

            if not assessment:
                return False

            session.delete(assessment)
            session.commit()
            return True


__all__ = ["AssessmentDatabaseStore"]
