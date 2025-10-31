"""FastAPI application exposing the review workflow endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field, model_validator

from .models import ReviewAction, ReviewEvent
from .store import ReviewStore

DEFAULT_STORE_PATH = Path("data/reviews/review_state.json")


class ReviewEventResponse(BaseModel):
    reviewer: str
    action: ReviewAction
    timestamp: str
    comment: Optional[str] = None


class ReviewSummaryResponse(BaseModel):
    question_id: str
    current_status: str
    history: list[ReviewEventResponse] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    action: ReviewAction
    comment: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_comment(self) -> "ReviewRequest":  # noqa: B902 - method signature defined by pydantic
        if self.action is ReviewAction.COMMENT and not self.comment:
            raise ValueError("comment is required when action is 'comment'")
        return self


def _get_default_store() -> ReviewStore:
    return ReviewStore(DEFAULT_STORE_PATH)


def create_app(store: Optional[ReviewStore] = None) -> FastAPI:
    app = FastAPI(title="MS2 QBank Review API")

    def get_store() -> ReviewStore:
        return store or _get_default_store()

    @app.get("/questions/{question_id}/reviews", response_model=ReviewSummaryResponse)
    def get_review_summary(question_id: str, review_store: ReviewStore = Depends(get_store)) -> ReviewSummaryResponse:
        record = review_store.get(question_id)
        history = [
            ReviewEventResponse(
                reviewer=event.reviewer,
                action=event.action,
                timestamp=event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                comment=event.comment,
            )
            for event in record.events
        ]
        return ReviewSummaryResponse(
            question_id=question_id,
            current_status=record.current_status(),
            history=history,
        )

    @app.post("/questions/{question_id}/reviews", response_model=ReviewSummaryResponse)
    def submit_review(
        question_id: str,
        payload: ReviewRequest,
        review_store: ReviewStore = Depends(get_store),
    ) -> ReviewSummaryResponse:
        event = ReviewEvent(reviewer=payload.reviewer, action=payload.action, comment=payload.comment)
        record = review_store.append(question_id, event)
        history = [
            ReviewEventResponse(
                reviewer=evt.reviewer,
                action=evt.action,
                timestamp=evt.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                comment=evt.comment,
            )
            for evt in record.events
        ]
        return ReviewSummaryResponse(
            question_id=question_id,
            current_status=record.current_status(),
            history=history,
        )

    return app


app = create_app()
