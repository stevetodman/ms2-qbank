"""FastAPI service orchestrating simulated assessment workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional

from fastapi import Depends, FastAPI, HTTPException

from analytics.service import AnalyticsService
from analytics.hooks import AssessmentAnalyticsHook
from .models import (
    AssessmentBlueprint,
    AssessmentCreateResponse,
    AssessmentScoreResponse,
    AssessmentStartResponse,
    AssessmentSubmissionResponse,
    AssessmentSubmitRequest,
)
from .store import AssessmentStore

_DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "questions"


def _load_question_payloads(directory: Path) -> list[dict]:
    questions: list[dict] = []
    if not directory.exists():
        return questions
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive handling
            raise RuntimeError(f"Failed to parse question dataset: {path}") from exc
        if isinstance(payload, list):
            questions.extend([item for item in payload if isinstance(item, Mapping)])
        elif isinstance(payload, Mapping):
            questions.append(dict(payload))
    return questions


class AssessmentDependencies:
    """Container wiring dependencies for request handlers."""

    def __init__(self, store: AssessmentStore) -> None:
        self.store = store

    def get_store(self) -> AssessmentStore:
        return self.store


def create_app(
    *,
    questions: Optional[Iterable[Mapping[str, object]]] = None,
    analytics_service: Optional[AnalyticsService] = None,
    question_count: int = 160,
    analytics_hook: Optional[AssessmentAnalyticsHook] = None,
) -> FastAPI:
    """Create a configured FastAPI application for the assessment workflow."""

    dataset = [dict(q) for q in questions] if questions is not None else _load_question_payloads(_DATA_DIRECTORY)
    service = analytics_service or AnalyticsService()
    hook = analytics_hook or AssessmentAnalyticsHook(scheduler=service.scheduler)
    store = AssessmentStore(dataset, question_count=question_count, analytics_hook=hook)

    app = FastAPI(title="MS2 QBank Assessment API")
    app.state.assessment_store = store
    app.state.analytics_service = service
    app.include_router(service.router)

    @app.on_event("startup")
    async def _startup() -> None:
        await service.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await service.shutdown()

    deps = AssessmentDependencies(store)

    def get_store() -> AssessmentStore:
        return deps.get_store()

    @app.post("/assessments", response_model=AssessmentCreateResponse)
    def create_assessment(payload: AssessmentBlueprint, store: AssessmentStore = Depends(get_store)) -> AssessmentCreateResponse:
        try:
            record = store.create(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return AssessmentCreateResponse(
            assessment_id=record.assessment_id,
            question_count=store.question_count,
            status=record.status,
        )

    @app.post("/assessments/{assessment_id}/start", response_model=AssessmentStartResponse)
    def start_assessment(assessment_id: str, store: AssessmentStore = Depends(get_store)) -> AssessmentStartResponse:
        try:
            record = store.start(assessment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        questions = store.question_payload(record)
        return AssessmentStartResponse(
            assessment_id=record.assessment_id,
            started_at=record.started_at or datetime.now(timezone.utc),
            expires_at=record.expires_at,
            time_limit_seconds=(
                int((record.expires_at - record.started_at).total_seconds())
                if record.expires_at and record.started_at
                else None
            ),
            questions=questions,
        )

    @app.post("/assessments/{assessment_id}/submit", response_model=AssessmentSubmissionResponse)
    def submit_assessment(
        assessment_id: str,
        payload: AssessmentSubmitRequest,
        store: AssessmentStore = Depends(get_store),
    ) -> AssessmentSubmissionResponse:
        try:
            record = store.submit(
                assessment_id,
                {item.question_id: item.answer for item in payload.responses},
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not record.score or not record.submitted_at:
            raise HTTPException(status_code=500, detail="Failed to score assessment")

        return AssessmentSubmissionResponse(
            assessment_id=record.assessment_id,
            submitted_at=record.submitted_at,
            score=record.score,
        )

    @app.get("/assessments/{assessment_id}/score", response_model=AssessmentScoreResponse)
    def get_score(assessment_id: str, store: AssessmentStore = Depends(get_store)) -> AssessmentScoreResponse:
        try:
            record = store.get(assessment_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        if record.status != "completed" or not record.score or not record.submitted_at:
            raise HTTPException(status_code=409, detail="Assessment has not been submitted")

        return AssessmentScoreResponse(
            assessment_id=record.assessment_id,
            completed_at=record.submitted_at,
            score=record.score,
        )

    return app


__all__ = ["create_app"]
