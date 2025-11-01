"""Database and API models for video library."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Column, DateTime, Field as SQLField, SQLModel, Text


# ===== DATABASE MODELS =====


class VideoDB(SQLModel, table=True):
    """Video content in the library."""

    __tablename__ = "videos"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str = SQLField(max_length=255, index=True)
    description: str = SQLField(sa_column=Column(Text))
    video_url: str = SQLField(max_length=500)  # URL to video file or embed
    thumbnail_url: Optional[str] = SQLField(default=None, max_length=500)
    duration_seconds: int  # Video duration in seconds

    # Categorization
    subject: str = SQLField(max_length=100, index=True)  # e.g., "Cardiology", "Anatomy"
    system: str = SQLField(max_length=100, index=True)  # e.g., "Cardiovascular", "Respiratory"
    topic: Optional[str] = SQLField(default=None, max_length=255)  # Specific topic

    # Metadata
    instructor: Optional[str] = SQLField(default=None, max_length=255)
    difficulty: str = SQLField(default="Medium", max_length=50)  # Easy, Medium, Hard
    tags: Optional[str] = SQLField(default=None, max_length=500)  # Comma-separated tags

    # Stats
    view_count: int = SQLField(default=0)

    # Timestamps
    created_at: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )


class PlaylistDB(SQLModel, table=True):
    """User-created or curated playlists."""

    __tablename__ = "playlists"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: Optional[int] = SQLField(default=None, index=True)  # None for official playlists
    name: str = SQLField(max_length=255)
    description: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    is_official: bool = SQLField(default=False)  # Official curated playlists

    # Timestamps
    created_at: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )


class PlaylistVideoDB(SQLModel, table=True):
    """Many-to-many relationship between playlists and videos."""

    __tablename__ = "playlist_videos"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    playlist_id: int = SQLField(foreign_key="playlists.id", index=True)
    video_id: int = SQLField(foreign_key="videos.id", index=True)
    position: int  # Order in playlist


class VideoProgressDB(SQLModel, table=True):
    """Track user progress watching videos."""

    __tablename__ = "video_progress"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(index=True)
    video_id: int = SQLField(foreign_key="videos.id", index=True)
    progress_seconds: int  # How far they watched
    completed: bool = SQLField(default=False)  # Finished watching
    last_watched: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )


class VideoBookmarkDB(SQLModel, table=True):
    """User bookmarks for specific timestamps in videos."""

    __tablename__ = "video_bookmarks"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(index=True)
    video_id: int = SQLField(foreign_key="videos.id", index=True)
    timestamp_seconds: int
    note: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    created_at: datetime = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )


# ===== API REQUEST/RESPONSE MODELS =====


class VideoCreate(BaseModel):
    """Request model for creating a video."""

    title: str
    description: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: int
    subject: str
    system: str
    topic: Optional[str] = None
    instructor: Optional[str] = None
    difficulty: str = "Medium"
    tags: Optional[str] = None


class VideoUpdate(BaseModel):
    """Request model for updating a video."""

    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    subject: Optional[str] = None
    system: Optional[str] = None
    topic: Optional[str] = None
    instructor: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[str] = None


class VideoResponse(BaseModel):
    """Response model for video."""

    id: int
    title: str
    description: str
    video_url: str
    thumbnail_url: Optional[str]
    duration_seconds: int
    subject: str
    system: str
    topic: Optional[str]
    instructor: Optional[str]
    difficulty: str
    tags: Optional[str]
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistCreate(BaseModel):
    """Request model for creating a playlist."""

    name: str
    description: Optional[str] = None


class PlaylistUpdate(BaseModel):
    """Request model for updating a playlist."""

    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistResponse(BaseModel):
    """Response model for playlist."""

    id: int
    user_id: Optional[int]
    name: str
    description: Optional[str]
    is_official: bool
    video_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistAddVideo(BaseModel):
    """Request to add video to playlist."""

    video_id: int


class VideoProgressUpdate(BaseModel):
    """Update video progress."""

    video_id: int
    progress_seconds: int
    completed: bool = False


class VideoProgressResponse(BaseModel):
    """Video progress response."""

    id: int
    user_id: int
    video_id: int
    progress_seconds: int
    completed: bool
    last_watched: datetime

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    """Create a video bookmark."""

    video_id: int
    timestamp_seconds: int
    note: Optional[str] = None


class BookmarkResponse(BaseModel):
    """Video bookmark response."""

    id: int
    user_id: int
    video_id: int
    timestamp_seconds: int
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
