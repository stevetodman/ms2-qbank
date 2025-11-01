"""Database models for medical library persistence."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy import JSON, Text
from pydantic import BaseModel


# Database Models
class ArticleDB(SQLModel, table=True):
    """Medical article stored in database."""
    __tablename__ = "articles"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    article_id: str = SQLField(unique=True, index=True, max_length=255)
    title: str = SQLField(max_length=500, index=True)
    summary: str = SQLField(sa_column=Column(Text))
    body: str = SQLField(sa_column=Column(Text))
    tags: str = SQLField(sa_column=Column(JSON), default="[]")  # JSON list
    bookmarked: bool = SQLField(default=False, index=True)

    # Metadata
    author: Optional[str] = SQLField(max_length=255)
    created_at: datetime = SQLField(index=True)
    updated_at: datetime = SQLField(index=True)


class NotebookEntryDB(SQLModel, table=True):
    """Notebook entry stored in database."""
    __tablename__ = "notebook_entries"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    note_id: str = SQLField(unique=True, index=True, max_length=255)
    user_id: Optional[int] = SQLField(index=True)  # User who created the note
    title: str = SQLField(max_length=500, index=True)
    body: str = SQLField(sa_column=Column(Text))
    tags: str = SQLField(sa_column=Column(JSON), default="[]")  # JSON list
    bookmarked: bool = SQLField(default=False, index=True)

    # Linked resources (JSON lists)
    article_ids: str = SQLField(sa_column=Column(JSON), default="[]")
    question_ids: str = SQLField(sa_column=Column(JSON), default="[]")
    video_ids: str = SQLField(sa_column=Column(JSON), default="[]")

    # Metadata
    created_at: datetime = SQLField(index=True)
    updated_at: datetime = SQLField(index=True)


# API Request/Response Models
class ArticleCreate(BaseModel):
    """Request to create an article."""
    article_id: str
    title: str
    summary: str
    body: str
    tags: list[str] = []
    author: Optional[str] = None


class ArticleUpdate(BaseModel):
    """Request to update an article."""
    title: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None
    author: Optional[str] = None


class ArticleResponse(BaseModel):
    """Article response."""
    id: str
    title: str
    summary: str
    body: str
    tags: list[str]
    bookmarked: bool
    author: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    """Request to create a notebook entry."""
    title: str
    body: str
    tags: list[str] = []
    article_ids: list[str] = []
    question_ids: list[str] = []
    video_ids: list[str] = []


class NoteUpdate(BaseModel):
    """Request to update a notebook entry."""
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None
    article_ids: Optional[list[str]] = None
    question_ids: Optional[list[str]] = None
    video_ids: Optional[list[str]] = None


class NoteResponse(BaseModel):
    """Notebook entry response."""
    id: str
    title: str
    body: str
    tags: list[str]
    article_ids: list[str]
    question_ids: list[str]
    video_ids: list[str]
    bookmarked: bool
    created_at: datetime
    updated_at: datetime


class BookmarkRequest(BaseModel):
    """Request to update bookmark status."""
    bookmarked: bool


class BookmarkResponse(BaseModel):
    """Response after updating bookmark."""
    id: str
    bookmarked: bool
