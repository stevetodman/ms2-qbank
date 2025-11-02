"""Database operations for video library."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select

from db_utils import create_hardened_sqlite_engine, run_migrations_for_engine
from .models import (
    PlaylistDB,
    PlaylistVideoDB,
    VideoBookmarkDB,
    VideoDB,
    VideoProgressDB,
)


class VideoStore:
    """Manages video library persistence."""

    def __init__(self, database_url: str = "sqlite:///data/videos.db"):
        """Initialize the video store.

        Args:
            database_url: SQLAlchemy database URL
        """
        # Ensure data directory exists
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine: Engine = create_hardened_sqlite_engine(database_url)
        SQLModel.metadata.create_all(self.engine)
        run_migrations_for_engine(self.engine, Path(__file__).parent / "migrations")

    # ===== VIDEO OPERATIONS =====

    def create_video(
        self,
        title: str,
        description: str,
        video_url: str,
        duration_seconds: int,
        subject: str,
        system: str,
        thumbnail_url: Optional[str] = None,
        topic: Optional[str] = None,
        instructor: Optional[str] = None,
        difficulty: str = "Medium",
        tags: Optional[str] = None,
    ) -> VideoDB:
        """Create a new video."""
        video = VideoDB(
            title=title,
            description=description,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration_seconds=duration_seconds,
            subject=subject,
            system=system,
            topic=topic,
            instructor=instructor,
            difficulty=difficulty,
            tags=tags,
        )

        with Session(self.engine) as session:
            session.add(video)
            session.commit()
            session.refresh(video)
            return video

    def get_video(self, video_id: int) -> Optional[VideoDB]:
        """Get a video by ID."""
        with Session(self.engine) as session:
            return session.get(VideoDB, video_id)

    def list_videos(
        self,
        subject: Optional[str] = None,
        system: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[VideoDB]:
        """List videos with optional filters."""
        with Session(self.engine) as session:
            statement = select(VideoDB)

            if subject:
                statement = statement.where(VideoDB.subject == subject)
            if system:
                statement = statement.where(VideoDB.system == system)
            if difficulty:
                statement = statement.where(VideoDB.difficulty == difficulty)

            statement = statement.order_by(VideoDB.created_at.desc())

            if limit:
                statement = statement.limit(limit)

            return list(session.exec(statement).all())

    def update_video(self, video_id: int, **kwargs) -> Optional[VideoDB]:
        """Update a video."""
        with Session(self.engine) as session:
            video = session.get(VideoDB, video_id)
            if not video:
                return None

            for key, value in kwargs.items():
                if value is not None and hasattr(video, key):
                    setattr(video, key, value)

            session.add(video)
            session.commit()
            session.refresh(video)
            return video

    def delete_video(self, video_id: int) -> bool:
        """Delete a video."""
        with Session(self.engine) as session:
            video = session.get(VideoDB, video_id)
            if not video:
                return False

            session.delete(video)
            session.commit()
            return True

    def increment_view_count(self, video_id: int) -> None:
        """Increment the view count for a video."""
        with Session(self.engine) as session:
            video = session.get(VideoDB, video_id)
            if video:
                video.view_count += 1
                session.add(video)
                session.commit()

    # ===== PLAYLIST OPERATIONS =====

    def create_playlist(
        self,
        name: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        is_official: bool = False,
    ) -> PlaylistDB:
        """Create a new playlist."""
        playlist = PlaylistDB(
            name=name,
            user_id=user_id,
            description=description,
            is_official=is_official,
        )

        with Session(self.engine) as session:
            session.add(playlist)
            session.commit()
            session.refresh(playlist)
            return playlist

    def get_playlist(self, playlist_id: int) -> Optional[PlaylistDB]:
        """Get a playlist by ID."""
        with Session(self.engine) as session:
            return session.get(PlaylistDB, playlist_id)

    def list_playlists(self, user_id: Optional[int] = None, official_only: bool = False) -> list[PlaylistDB]:
        """List playlists."""
        with Session(self.engine) as session:
            statement = select(PlaylistDB)

            if official_only:
                statement = statement.where(PlaylistDB.is_official == True)
            elif user_id is not None:
                statement = statement.where(
                    (PlaylistDB.user_id == user_id) | (PlaylistDB.is_official == True)
                )

            statement = statement.order_by(PlaylistDB.created_at.desc())
            return list(session.exec(statement).all())

    def add_video_to_playlist(self, playlist_id: int, video_id: int) -> PlaylistVideoDB:
        """Add a video to a playlist."""
        with Session(self.engine) as session:
            # Get current max position
            statement = (
                select(PlaylistVideoDB)
                .where(PlaylistVideoDB.playlist_id == playlist_id)
                .order_by(PlaylistVideoDB.position.desc())
            )
            last_item = session.exec(statement).first()
            position = (last_item.position + 1) if last_item else 0

            playlist_video = PlaylistVideoDB(
                playlist_id=playlist_id,
                video_id=video_id,
                position=position,
            )

            session.add(playlist_video)
            session.commit()
            session.refresh(playlist_video)
            return playlist_video

    def get_playlist_videos(self, playlist_id: int) -> list[VideoDB]:
        """Get all videos in a playlist in order."""
        with Session(self.engine) as session:
            statement = (
                select(VideoDB)
                .join(PlaylistVideoDB, VideoDB.id == PlaylistVideoDB.video_id)
                .where(PlaylistVideoDB.playlist_id == playlist_id)
                .order_by(PlaylistVideoDB.position)
            )
            return list(session.exec(statement).all())

    def get_playlist_video_count(self, playlist_id: int) -> int:
        """Get the number of videos in a playlist."""
        with Session(self.engine) as session:
            statement = select(PlaylistVideoDB).where(PlaylistVideoDB.playlist_id == playlist_id)
            return len(list(session.exec(statement).all()))

    def remove_video_from_playlist(self, playlist_id: int, video_id: int) -> bool:
        """Remove a video from a playlist."""
        with Session(self.engine) as session:
            statement = select(PlaylistVideoDB).where(
                (PlaylistVideoDB.playlist_id == playlist_id) & (PlaylistVideoDB.video_id == video_id)
            )
            playlist_video = session.exec(statement).first()

            if not playlist_video:
                return False

            session.delete(playlist_video)
            session.commit()
            return True

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist and all its associations."""
        with Session(self.engine) as session:
            playlist = session.get(PlaylistDB, playlist_id)
            if not playlist:
                return False

            # Delete all playlist-video associations
            statement = select(PlaylistVideoDB).where(PlaylistVideoDB.playlist_id == playlist_id)
            for pv in session.exec(statement).all():
                session.delete(pv)

            session.delete(playlist)
            session.commit()
            return True

    # ===== VIDEO PROGRESS OPERATIONS =====

    def update_progress(
        self,
        user_id: int,
        video_id: int,
        progress_seconds: int,
        completed: bool = False,
    ) -> VideoProgressDB:
        """Update or create video progress."""
        with Session(self.engine) as session:
            statement = select(VideoProgressDB).where(
                (VideoProgressDB.user_id == user_id) & (VideoProgressDB.video_id == video_id)
            )
            progress = session.exec(statement).first()

            if progress:
                progress.progress_seconds = progress_seconds
                progress.completed = completed
            else:
                progress = VideoProgressDB(
                    user_id=user_id,
                    video_id=video_id,
                    progress_seconds=progress_seconds,
                    completed=completed,
                )

            session.add(progress)
            session.commit()
            session.refresh(progress)
            return progress

    def get_progress(self, user_id: int, video_id: int) -> Optional[VideoProgressDB]:
        """Get user's progress for a specific video."""
        with Session(self.engine) as session:
            statement = select(VideoProgressDB).where(
                (VideoProgressDB.user_id == user_id) & (VideoProgressDB.video_id == video_id)
            )
            return session.exec(statement).first()

    # ===== BOOKMARK OPERATIONS =====

    def create_bookmark(
        self,
        user_id: int,
        video_id: int,
        timestamp_seconds: int,
        note: Optional[str] = None,
    ) -> VideoBookmarkDB:
        """Create a video bookmark."""
        bookmark = VideoBookmarkDB(
            user_id=user_id,
            video_id=video_id,
            timestamp_seconds=timestamp_seconds,
            note=note,
        )

        with Session(self.engine) as session:
            session.add(bookmark)
            session.commit()
            session.refresh(bookmark)
            return bookmark

    def get_bookmarks(self, user_id: int, video_id: int) -> list[VideoBookmarkDB]:
        """Get all bookmarks for a video."""
        with Session(self.engine) as session:
            statement = (
                select(VideoBookmarkDB)
                .where((VideoBookmarkDB.user_id == user_id) & (VideoBookmarkDB.video_id == video_id))
                .order_by(VideoBookmarkDB.timestamp_seconds)
            )
            return list(session.exec(statement).all())

    def delete_bookmark(self, bookmark_id: int, user_id: int) -> bool:
        """Delete a bookmark."""
        with Session(self.engine) as session:
            statement = select(VideoBookmarkDB).where(
                (VideoBookmarkDB.id == bookmark_id) & (VideoBookmarkDB.user_id == user_id)
            )
            bookmark = session.exec(statement).first()

            if not bookmark:
                return False

            session.delete(bookmark)
            session.commit()
            return True
