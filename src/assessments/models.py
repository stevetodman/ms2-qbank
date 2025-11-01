"""Pydantic models and domain helpers for the assessment service."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from pydantic import BaseModel, Field, field_validator


class AssessmentBlueprint(BaseModel):
    """Filter and configuration inputs provided when creating an assessment."""

    candidate_id: str = Field(..., min_length=1)
    subject: Optional[str] = Field(default=None, description="Subject focus filter")
    system: Optional[str] = Field(default=None, description="Organ system filter")
    difficulty: Optional[str] = Field(default=None, description="Difficulty filter")
    tags: list[str] = Field(default_factory=list, description="Tag filters")
    time_limit_minutes: int = Field(
        default=280,
        ge=30,
        le=600,
        description="Total time limit for the assessment in minutes",
    )

    @field_validator("tags")
    @classmethod
    def _strip_tags(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for raw in values:
            tag = raw.strip()
            if not tag:
                raise ValueError("tags must not be empty strings")
            cleaned.append(tag)
        return cleaned


class AssessmentCreateResponse(BaseModel):
    assessment_id: str
    question_count: int
    status: str


class ChoicePayload(BaseModel):
    label: str
    text: str


class AssessmentQuestion(BaseModel):
    id: str
    stem: str
    choices: list[ChoicePayload]


class AssessmentStartResponse(BaseModel):
    assessment_id: str
    started_at: datetime
    expires_at: Optional[datetime]
    time_limit_seconds: Optional[int]
    questions: list[AssessmentQuestion]


class AssessmentResponseItem(BaseModel):
    question_id: str
    answer: Optional[str] = None


class AssessmentSubmitRequest(BaseModel):
    responses: list[AssessmentResponseItem]

    @field_validator("responses")
    @classmethod
    def _ensure_unique_questions(
        cls, values: Iterable[AssessmentResponseItem]
    ) -> Iterable[AssessmentResponseItem]:
        seen: set[str] = set()
        for item in values:
            if item.question_id in seen:
                raise ValueError("duplicate question_id in responses")
            seen.add(item.question_id)
        return values


class AssessmentScoreBreakdown(BaseModel):
    total_questions: int
    correct: int
    incorrect: int
    omitted: int
    percentage: float
    duration_seconds: Optional[int]


class AssessmentSubmissionResponse(BaseModel):
    assessment_id: str
    submitted_at: datetime
    score: AssessmentScoreBreakdown


class AssessmentScoreResponse(BaseModel):
    assessment_id: str
    completed_at: datetime
    score: AssessmentScoreBreakdown


__all__ = [
    "AssessmentBlueprint",
    "AssessmentCreateResponse",
    "ChoicePayload",
    "AssessmentQuestion",
    "AssessmentStartResponse",
    "AssessmentResponseItem",
    "AssessmentSubmitRequest",
    "AssessmentScoreBreakdown",
    "AssessmentSubmissionResponse",
    "AssessmentScoreResponse",
]
