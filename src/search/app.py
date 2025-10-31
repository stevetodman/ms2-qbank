"""FastAPI application exposing the :class:`QuestionIndex` search surface."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .index import QuestionIndex

# Directory containing question JSON payloads. The default points to the
# repository's ``data/questions`` folder.
DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "questions"
ANALYTICS_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "analytics"


def _load_question_payloads(directory: Path) -> List[Dict[str, Any]]:
    """Load all question payloads from ``directory``.

    Each ``*.json`` file is expected to contain either a list of questions or a
    single question mapping. The loader is intentionally flexible to simplify
    authoring fixtures during development.
    """

    questions: List[Dict[str, Any]] = []
    if not directory.exists():
        return questions

    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        if isinstance(payload, list):
            questions.extend([item for item in payload if isinstance(item, dict)])
        elif isinstance(payload, dict):
            questions.append(payload)
    return questions


class Pagination(BaseModel):
    """Metadata describing the window of results returned."""

    total: int = Field(..., ge=0, description="Total number of matches")
    limit: int = Field(..., ge=1, description="Requested maximum number of items")
    offset: int = Field(..., ge=0, description="Zero-based starting index of results")
    returned: int = Field(..., ge=0, description="Number of items included in the response")


class SearchRequest(BaseModel):
    """Incoming search request payload."""

    query: Optional[str] = Field(default=None, description="Full-text query string")
    tags: Optional[List[str]] = Field(default=None, description="List of tags to match")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata filters applied to question metadata"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based index into the matching result set",
    )


class SearchResponse(BaseModel):
    """Search response payload including pagination details."""

    data: List[Dict[str, Any]]
    pagination: Pagination


class UsageDistributionBucket(BaseModel):
    """Histogram bucket describing usage distribution."""

    deliveries: int = Field(..., ge=0, description="Number of deliveries represented by the bucket")
    questions: int = Field(..., ge=0, description="Number of questions that fall into the bucket")


class AnalyticsUsageSummary(BaseModel):
    """Usage summary included in analytics responses."""

    tracked_questions: int = Field(..., ge=0)
    total_usage: int = Field(..., ge=0)
    average_usage: float = Field(..., ge=0)
    minimum_usage: int = Field(..., ge=0)
    maximum_usage: int = Field(..., ge=0)
    usage_distribution: List[UsageDistributionBucket]


class AnalyticsMetrics(BaseModel):
    """Top-level analytics payload returned to clients."""

    total_questions: int = Field(..., ge=0)
    difficulty_distribution: Dict[str, int]
    review_status_distribution: Dict[str, int]
    usage_summary: AnalyticsUsageSummary


class AnalyticsArtifact(BaseModel):
    """Relative paths to generated analytics artifacts."""

    json_path: str = Field(..., description="Relative path to the JSON artifact in data/analytics")
    markdown_path: str = Field(..., description="Relative path to the markdown artifact in data/analytics")


class AnalyticsResponse(BaseModel):
    """Response describing the most recent analytics report."""

    generated_at: str = Field(..., description="ISO-8601 timestamp for the analytics snapshot")
    metrics: AnalyticsMetrics
    artifact: AnalyticsArtifact


def _initialise_index() -> QuestionIndex:
    questions = _load_question_payloads(DATA_DIRECTORY)
    return QuestionIndex(questions)


app = FastAPI(title="MS2 Question Search API", version="1.0.0")


@app.on_event("startup")
def _load_index() -> None:
    app.state.index = _initialise_index()


def _get_index() -> QuestionIndex:
    index = getattr(app.state, "index", None)
    if index is None:
        raise HTTPException(status_code=500, detail="Search index is not initialised")
    return index


_TIMESTAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z\.json$")


def _load_latest_analytics() -> Dict[str, Any]:
    if not ANALYTICS_DIRECTORY.exists():
        raise HTTPException(status_code=404, detail="No analytics have been generated")

    candidates = sorted(
        path for path in ANALYTICS_DIRECTORY.glob("*.json") if _TIMESTAMP_PATTERN.match(path.name)
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="No analytics have been generated")

    latest = candidates[-1]
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - unexpected data corruption
        raise HTTPException(status_code=500, detail="Failed to parse analytics artifact") from exc

    metrics = payload.get("metrics")
    generated_at = payload.get("generated_at")
    if not isinstance(metrics, dict) or not isinstance(generated_at, str):
        raise HTTPException(status_code=500, detail="Latest analytics artifact is invalid")

    usage_summary = metrics.get("usage_summary")
    if not isinstance(usage_summary, dict):
        raise HTTPException(status_code=500, detail="Latest analytics artifact is invalid")

    distribution = usage_summary.get("usage_distribution", {})
    buckets: List[Dict[str, int]] = []
    if isinstance(distribution, dict):
        for key, value in distribution.items():
            try:
                deliveries = int(key)
            except (TypeError, ValueError):
                continue
            if not isinstance(value, int):
                continue
            buckets.append({"deliveries": deliveries, "questions": value})
    elif isinstance(distribution, list):
        for entry in distribution:
            if not isinstance(entry, dict):
                continue
            deliveries = entry.get("deliveries")
            questions = entry.get("questions")
            if isinstance(deliveries, int) and isinstance(questions, int):
                buckets.append({"deliveries": deliveries, "questions": questions})
    buckets.sort(key=lambda item: item["deliveries"])

    usage_summary = {
        "tracked_questions": usage_summary.get("tracked_questions", 0),
        "total_usage": usage_summary.get("total_usage", 0),
        "average_usage": usage_summary.get("average_usage", 0.0),
        "minimum_usage": usage_summary.get("minimum_usage", 0),
        "maximum_usage": usage_summary.get("maximum_usage", 0),
        "usage_distribution": buckets,
    }

    metrics_payload = {
        "total_questions": metrics.get("total_questions", 0),
        "difficulty_distribution": metrics.get("difficulty_distribution", {}),
        "review_status_distribution": metrics.get("review_status_distribution", {}),
        "usage_summary": usage_summary,
    }

    artifact = {
        "json_path": latest.name,
        "markdown_path": latest.with_suffix(".md").name,
    }

    return {
        "generated_at": generated_at,
        "metrics": metrics_payload,
        "artifact": artifact,
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Search the question dataset using a combination of filters."""

    index = _get_index()
    matches = index.search(
        query=request.query,
        tags=request.tags,
        metadata_filters=request.metadata,
        limit=None,
    )

    total = len(matches)
    offset = request.offset
    limit = request.limit

    start = min(offset, total)
    end = min(start + limit, total)
    window = matches[start:end]

    pagination = Pagination(
        total=total,
        limit=limit,
        offset=start,
        returned=len(window),
    )

    return SearchResponse(data=window, pagination=pagination)


@app.get("/analytics/latest", response_model=AnalyticsResponse)
async def latest_analytics() -> AnalyticsResponse:
    """Return the most recently generated analytics snapshot."""

    payload = _load_latest_analytics()
    return AnalyticsResponse(**payload)


__all__ = [
    "app",
    "SearchRequest",
    "SearchResponse",
    "Pagination",
    "DATA_DIRECTORY",
    "ANALYTICS_DIRECTORY",
    "AnalyticsResponse",
]
