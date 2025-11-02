"""FastAPI application exposing the review workflow endpoints."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Sequence

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from logging_config import configure_logging, get_logger, RequestLoggingMiddleware
from analytics.service import AnalyticsService
from .auth import (
    AuthenticationMiddleware,
    AuthenticatedUser,
    bearer_jwt_resolver,
    get_current_user,
)
from .auth_providers import JWKSProviderConfig, JWKSFetcher, jwks_bearer_resolver, parse_provider_configs
from .models import InvalidTransitionError, ReviewAction, ReviewEvent, ReviewerRole
from .store import ReviewStore

# Configure structured logging
configure_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    service_name="reviews-api",
    json_format=(os.getenv("LOG_FORMAT", "json") == "json"),
)

logger = get_logger(__name__)

DEFAULT_STORE_PATH = Path("data/reviews/review_state.db")


class ReviewEventResponse(BaseModel):
    reviewer: str
    action: ReviewAction
    timestamp: str
    role: ReviewerRole
    comment: Optional[str] = None


class ReviewSummaryResponse(BaseModel):
    question_id: str
    current_status: str
    history: list[ReviewEventResponse] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    action: ReviewAction
    role: ReviewerRole
    comment: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_comment(self) -> "ReviewRequest":  # noqa: B902 - method signature defined by pydantic
        if self.action is ReviewAction.COMMENT and not self.comment:
            raise ValueError("comment is required when action is 'comment'")
        return self


def _get_default_store() -> ReviewStore:
    return ReviewStore(DEFAULT_STORE_PATH)


def _validate_role_for_action(
    action: ReviewAction,
    role: ReviewerRole,
    user: AuthenticatedUser,
) -> None:
    allowed_roles = {
        ReviewAction.COMMENT: {
            ReviewerRole.AUTHOR,
            ReviewerRole.REVIEWER,
            ReviewerRole.EDITOR,
            ReviewerRole.ADMIN,
        },
        ReviewAction.APPROVE: {ReviewerRole.EDITOR, ReviewerRole.ADMIN},
        ReviewAction.REJECT: {ReviewerRole.EDITOR, ReviewerRole.ADMIN},
    }
    if role not in allowed_roles[action]:
        raise HTTPException(status_code=403, detail=f"Role '{role.value}' cannot perform '{action.value}'")
    if role.value not in user.roles:
        raise HTTPException(status_code=403, detail="Authenticated user lacks required role")


def create_app(
    store: Optional[ReviewStore] = None,
    *,
    jwt_secret: Optional[str] = None,
    analytics_service: Optional[AnalyticsService] = None,
    jwks_providers: Optional[Sequence[JWKSProviderConfig]] = None,
    jwks_fetcher: Optional[JWKSFetcher] = None,
) -> FastAPI:
    configured_providers = list(jwks_providers or [])
    if not configured_providers:
        raw_config = os.getenv("REVIEWS_JWT_JWKS_PROVIDERS")
        if raw_config:
            try:
                configured_providers = parse_provider_configs(raw_config)
            except ValueError as exc:
                raise RuntimeError("Invalid JWKS provider configuration") from exc

    if configured_providers:
        resolver = jwks_bearer_resolver(configured_providers, fetcher=jwks_fetcher)
    else:
        secret = jwt_secret or os.getenv("REVIEWS_JWT_SECRET")
        if not secret:
            raise RuntimeError("JWT secret must be configured for the review API")
        resolver = bearer_jwt_resolver(secret)

    store_instance = store or _get_default_store()
    service = analytics_service or AnalyticsService()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Reviews API starting up")
        await service.start()
        store_instance.set_analytics_hook(service.handle_status_change)
        yield
        # Shutdown
        logger.info("Reviews API shutting down")
        store_instance.set_analytics_hook(None)
        await service.shutdown()

    app = FastAPI(title="MS2 QBank Review API", lifespan=lifespan)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware, resolver=resolver)

    app.state.review_store = store_instance
    app.state.analytics_service = service
    app.state.analytics_scheduler = service.scheduler
    app.include_router(service.router)

    logger.info("Reviews API initialized")

    def get_store() -> ReviewStore:
        return app.state.review_store

    def _allowed_actions(user: AuthenticatedUser) -> list[str]:
        roles = {role.lower() for role in user.roles}
        actions: list[str] = []
        if roles & {
            ReviewerRole.AUTHOR.value,
            ReviewerRole.REVIEWER.value,
            ReviewerRole.EDITOR.value,
            ReviewerRole.ADMIN.value,
        }:
            actions.append(ReviewAction.COMMENT.value)
        if roles & {ReviewerRole.EDITOR.value, ReviewerRole.ADMIN.value}:
            actions.extend([ReviewAction.APPROVE.value, ReviewAction.REJECT.value])
        return actions

    @app.get("/questions/{question_id}/reviews", response_model=ReviewSummaryResponse)
    def get_review_summary(
        question_id: str,
        review_store: ReviewStore = Depends(get_store),
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> ReviewSummaryResponse:
        record = review_store.get(question_id)
        history = [
            ReviewEventResponse(
                reviewer=event.reviewer,
                action=event.action,
                timestamp=event.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                role=event.role,
                comment=event.comment,
            )
            for event in record.events
        ]
        return ReviewSummaryResponse(
            question_id=question_id,
            current_status=record.current_status(),
            history=history,
            allowed_actions=_allowed_actions(user),
        )

    @app.post("/questions/{question_id}/reviews", response_model=ReviewSummaryResponse)
    def submit_review(
        question_id: str,
        payload: ReviewRequest,
        review_store: ReviewStore = Depends(get_store),
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> ReviewSummaryResponse:
        _validate_role_for_action(payload.action, payload.role, user)
        event = ReviewEvent(
            reviewer=payload.reviewer,
            action=payload.action,
            role=payload.role,
            comment=payload.comment,
        )
        try:
            record = review_store.append(question_id, event)
        except InvalidTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        history = [
            ReviewEventResponse(
                reviewer=evt.reviewer,
                action=evt.action,
                timestamp=evt.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                role=evt.role,
                comment=evt.comment,
            )
            for evt in record.events
        ]
        return ReviewSummaryResponse(
            question_id=question_id,
            current_status=record.current_status(),
            history=history,
            allowed_actions=_allowed_actions(user),
        )

    return app
try:
    app = create_app()
except RuntimeError:
    app = FastAPI(title="MS2 QBank Review API")
