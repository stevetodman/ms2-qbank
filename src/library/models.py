"""Pydantic models for the library service."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Represents a medical library article."""

    id: str
    title: str
    summary: str
    body: str
    tags: List[str] = Field(default_factory=list)
    bookmarked: bool = False


class NotebookEntry(BaseModel):
    """Represents a notebook entry created by learners."""

    id: str
    title: str
    body: str
    tags: List[str] = Field(default_factory=list)
    article_ids: List[str] = Field(default_factory=list)
    question_ids: List[str] = Field(default_factory=list)
    bookmarked: bool = False


class ArticleQuery(BaseModel):
    """Query parameters for filtering articles."""

    query: Optional[str] = None
    tag: Optional[str] = None


class NoteQuery(BaseModel):
    """Query parameters for filtering notebook entries."""

    query: Optional[str] = None
    tag: Optional[str] = None
    article_id: Optional[str] = None
    question_id: Optional[str] = None


class CreateNoteRequest(BaseModel):
    """Payload for creating a notebook entry."""

    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    article_ids: List[str] = Field(default_factory=list)
    question_ids: List[str] = Field(default_factory=list)


class UpdateNoteRequest(BaseModel):
    """Payload for updating notebook entries."""

    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    article_ids: Optional[List[str]] = None
    question_ids: Optional[List[str]] = None


class LinkReviewRequest(BaseModel):
    """Payload for linking a note to a reviewed question."""

    question_id: str = Field(..., min_length=1)


class BookmarkResponse(BaseModel):
    """Response returned after toggling bookmark state."""

    id: str
    bookmarked: bool


class BookmarkRequest(BaseModel):
    """Request payload for setting bookmark state."""

    bookmarked: bool
