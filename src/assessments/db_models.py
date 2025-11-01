"""Database models for self-assessment persistence."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy import JSON
from pydantic import BaseModel


# Database Models
class AssessmentDB(SQLModel, table=True):
    """Persistent record of an assessment."""
    __tablename__ = "assessments"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    assessment_id: str = SQLField(unique=True, index=True, max_length=255)
    candidate_id: str = SQLField(index=True, max_length=255)

    # Blueprint (filter configuration)
    subject: Optional[str] = SQLField(max_length=100)
    system: Optional[str] = SQLField(max_length=100)
    difficulty: Optional[str] = SQLField(max_length=50)
    tags: str = SQLField(sa_column=Column(JSON), default="[]")  # JSON list
    time_limit_minutes: int = SQLField(default=280)

    # Status and timestamps
    status: str = SQLField(max_length=50, default="created", index=True)
    created_at: datetime = SQLField(index=True)
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

    # Question delivery (stored as JSON)
    question_ids: str = SQLField(sa_column=Column(JSON), default="[]")  # JSON list

    # Responses (stored as JSON)
    responses: str = SQLField(sa_column=Column(JSON), default="{}")  # JSON object

    # Score
    total_questions: int = SQLField(default=0)
    correct: int = SQLField(default=0)
    incorrect: int = SQLField(default=0)
    omitted: int = SQLField(default=0)
    percentage: float = SQLField(default=0.0)
    duration_seconds: Optional[int] = None


# API Request/Response Models
class AssessmentBlueprintCreate(BaseModel):
    """Request to create an assessment."""
    candidate_id: str
    subject: Optional[str] = None
    system: Optional[str] = None
    difficulty: Optional[str] = None
    tags: list[str] = []
    time_limit_minutes: int = 280


class AssessmentResponse(BaseModel):
    """Response with assessment metadata."""
    assessment_id: str
    candidate_id: str
    status: str
    question_count: int
    time_limit_minutes: int
    created_at: datetime
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AssessmentQuestionResponse(BaseModel):
    """A single question in an assessment."""
    id: str
    stem: str
    choices: list[dict]


class AssessmentStartResponse(BaseModel):
    """Response when starting an assessment."""
    assessment_id: str
    started_at: datetime
    expires_at: Optional[datetime]
    time_limit_seconds: Optional[int]
    questions: list[AssessmentQuestionResponse]


class AssessmentSubmitRequest(BaseModel):
    """Request to submit assessment responses."""
    responses: list[dict]  # List of {question_id, answer}


class AssessmentScoreResponse(BaseModel):
    """Assessment score breakdown."""
    total_questions: int
    correct: int
    incorrect: int
    omitted: int
    percentage: float
    duration_seconds: Optional[int]


class AssessmentSubmissionResponse(BaseModel):
    """Response after submitting an assessment."""
    assessment_id: str
    submitted_at: datetime
    score: AssessmentScoreResponse
