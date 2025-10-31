"""FastAPI application exposing the :class:`QuestionIndex` search surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .index import QuestionIndex

# Directory containing question JSON payloads. The default points to the
# repository's ``data/questions`` folder.
DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "questions"


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


__all__ = ["app", "SearchRequest", "SearchResponse", "Pagination", "DATA_DIRECTORY"]
