"""FastAPI application for user performance analytics."""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from users.auth import decode_access_token

from .user_store import UserAnalyticsStore
from .user_models import (
    AttemptCreate,
    UserAnalytics,
    PercentileRanking,
    QuestionAttemptDB,
)


def optional_auth(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """Optional authentication - returns user_id if token present, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_access_token(token)
        return payload.get("user_id")
    except Exception:
        return None


def get_current_user_id(authorization: str = Header(..., alias="Authorization")) -> int:
    """Required authentication - returns user_id or raises 401."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# Initialize FastAPI app
app = FastAPI(
    title="MS2 QBank User Analytics API",
    description="User performance tracking and analytics",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize store
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "analytics.db"
store = UserAnalyticsStore(db_path=str(DB_PATH))


@app.post("/attempts", response_model=dict)
async def record_attempt(
    attempt: AttemptCreate,
    user_id: Optional[int] = Depends(optional_auth),
) -> dict:
    """Record a question attempt."""
    try:
        recorded = store.record_attempt(
            user_id=user_id,
            question_id=attempt.question_id,
            assessment_id=attempt.assessment_id,
            subject=attempt.subject,
            system=attempt.system,
            difficulty=attempt.difficulty,
            answer_given=attempt.answer_given,
            correct_answer=attempt.correct_answer,
            is_correct=attempt.is_correct,
            time_seconds=attempt.time_seconds,
            mode=attempt.mode,
            marked=attempt.marked,
            omitted=attempt.omitted,
        )

        return {"success": True, "attempt_id": recorded.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@app.get("/attempts/recent", response_model=list[QuestionAttemptDB])
async def get_recent_attempts(
    limit: int = 50,
    subject: Optional[str] = None,
    system: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
) -> list[QuestionAttemptDB]:
    """Get recent attempts for the current user."""
    try:
        return store.get_user_attempts(
            user_id=user_id, limit=limit, subject=subject, system=system
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve attempts: {str(e)}")


@app.get("/analytics", response_model=UserAnalytics)
async def get_user_analytics(
    days: int = 30,
    user_id: int = Depends(get_current_user_id),
) -> UserAnalytics:
    """Get comprehensive analytics for the current user."""
    try:
        return store.compute_user_analytics(user_id=user_id, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute analytics: {str(e)}")


@app.get("/analytics/percentile", response_model=PercentileRanking)
async def get_percentile_ranking(
    user_id: int = Depends(get_current_user_id),
) -> PercentileRanking:
    """Get percentile ranking compared to all users."""
    try:
        return store.compute_percentile_ranking(user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute percentile ranking: {str(e)}"
        )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "user-analytics"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8008)
