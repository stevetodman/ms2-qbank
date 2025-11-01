"""Database models for user performance analytics."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field as SQLField
from pydantic import BaseModel


# Database Models
class QuestionAttemptDB(SQLModel, table=True):
    """Record of a single question attempt by a user."""
    __tablename__ = "question_attempts"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: Optional[int] = SQLField(index=True)
    question_id: str = SQLField(max_length=255, index=True)
    assessment_id: Optional[str] = SQLField(max_length=255, index=True)

    # Question metadata (denormalized for faster queries)
    subject: Optional[str] = SQLField(max_length=100, index=True)
    system: Optional[str] = SQLField(max_length=100, index=True)
    difficulty: Optional[str] = SQLField(max_length=50)

    # Attempt details
    answer_given: Optional[str] = SQLField(max_length=10)
    correct_answer: str = SQLField(max_length=10)
    is_correct: bool = SQLField(index=True)
    time_seconds: Optional[int] = None

    # Context
    mode: str = SQLField(max_length=50, default="practice")  # practice, assessment, tutor
    marked: bool = SQLField(default=False)
    omitted: bool = SQLField(default=False)

    # Timestamp
    attempted_at: datetime = SQLField(index=True)


class UserAnalyticsSummaryDB(SQLModel, table=True):
    """Aggregated analytics for a user (cached for performance)."""
    __tablename__ = "user_analytics_summary"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(unique=True, index=True)

    # Overall stats
    total_attempts: int = SQLField(default=0)
    correct_attempts: int = SQLField(default=0)
    incorrect_attempts: int = SQLField(default=0)
    omitted_attempts: int = SQLField(default=0)
    accuracy_percent: float = SQLField(default=0.0)

    # Time metrics
    average_time_seconds: float = SQLField(default=0.0)
    total_study_time_seconds: int = SQLField(default=0)

    # Progress tracking
    questions_attempted_count: int = SQLField(default=0)  # Unique questions
    assessments_completed: int = SQLField(default=0)

    # Timestamps
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    last_computed_at: datetime = SQLField(default_factory=datetime.utcnow)


# API Request/Response Models
class AttemptCreate(BaseModel):
    """Request to record a question attempt."""
    question_id: str
    assessment_id: Optional[str] = None
    subject: Optional[str] = None
    system: Optional[str] = None
    difficulty: Optional[str] = None
    answer_given: Optional[str] = None
    correct_answer: str
    is_correct: bool
    time_seconds: Optional[int] = None
    mode: str = "practice"
    marked: bool = False
    omitted: bool = False


class SubjectPerformance(BaseModel):
    """Performance metrics for a specific subject."""
    subject: str
    total_attempts: int
    correct: int
    incorrect: int
    accuracy_percent: float
    average_time_seconds: float


class SystemPerformance(BaseModel):
    """Performance metrics for a specific organ system."""
    system: str
    total_attempts: int
    correct: int
    incorrect: int
    accuracy_percent: float
    average_time_seconds: float


class DifficultyPerformance(BaseModel):
    """Performance metrics by difficulty level."""
    difficulty: str
    total_attempts: int
    correct: int
    incorrect: int
    accuracy_percent: float


class DailyPerformance(BaseModel):
    """Performance metrics for a specific day."""
    date: str
    total_attempts: int
    correct: int
    incorrect: int
    accuracy_percent: float
    study_time_seconds: int


class WeakArea(BaseModel):
    """Identification of a weak performance area."""
    category: str  # subject or system
    name: str
    total_attempts: int
    accuracy_percent: float
    rank: int  # Lower is worse


class UserAnalytics(BaseModel):
    """Comprehensive user performance analytics."""
    user_id: int

    # Overall metrics
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    omitted_attempts: int
    accuracy_percent: float
    average_time_seconds: float
    total_study_time_hours: float

    # Progress
    questions_attempted_count: int
    assessments_completed: int
    current_streak_days: int

    # Breakdowns
    by_subject: list[SubjectPerformance]
    by_system: list[SystemPerformance]
    by_difficulty: list[DifficultyPerformance]

    # Time series
    daily_performance: list[DailyPerformance]

    # Insights
    weak_areas: list[WeakArea]
    strongest_subject: Optional[str] = None
    weakest_subject: Optional[str] = None

    # Timestamps
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None


class PercentileRanking(BaseModel):
    """User's percentile ranking compared to peers."""
    user_id: int
    overall_percentile: float
    accuracy_percentile: float
    speed_percentile: float
    volume_percentile: float
    total_users: int
