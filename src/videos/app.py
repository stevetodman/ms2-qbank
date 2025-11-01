"""FastAPI application for video library."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status

from .models import (
    BookmarkCreate,
    BookmarkResponse,
    PlaylistAddVideo,
    PlaylistCreate,
    PlaylistResponse,
    PlaylistUpdate,
    VideoCreate,
    VideoProgressResponse,
    VideoProgressUpdate,
    VideoResponse,
    VideoUpdate,
)
from .store import VideoStore


def create_app(*, store: Optional[VideoStore] = None) -> FastAPI:
    """Create and configure the video library FastAPI application.

    Args:
        store: Optional VideoStore instance for dependency injection (testing)

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(title="MS2 QBank Video Library API", version="1.0.0")

    # Initialize video store
    video_store = store or VideoStore()
    app.state.video_store = video_store

    def get_store() -> VideoStore:
        """Dependency to get the video store instance."""
        return app.state.video_store

    # ===== VIDEO ENDPOINTS =====

    @app.post("/videos", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
    def create_video(
        payload: VideoCreate,
        store: VideoStore = Depends(get_store),
    ) -> VideoResponse:
        """Create a new video."""
        video = store.create_video(
            title=payload.title,
            description=payload.description,
            video_url=payload.video_url,
            duration_seconds=payload.duration_seconds,
            subject=payload.subject,
            system=payload.system,
            thumbnail_url=payload.thumbnail_url,
            topic=payload.topic,
            instructor=payload.instructor,
            difficulty=payload.difficulty,
            tags=payload.tags,
        )
        return VideoResponse.model_validate(video)

    @app.get("/videos", response_model=list[VideoResponse])
    def list_videos(
        subject: Optional[str] = None,
        system: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: Optional[int] = None,
        store: VideoStore = Depends(get_store),
    ) -> list[VideoResponse]:
        """List videos with optional filters."""
        videos = store.list_videos(
            subject=subject,
            system=system,
            difficulty=difficulty,
            limit=limit,
        )
        return [VideoResponse.model_validate(v) for v in videos]

    @app.get("/videos/{video_id}", response_model=VideoResponse)
    def get_video(
        video_id: int,
        store: VideoStore = Depends(get_store),
    ) -> VideoResponse:
        """Get a specific video."""
        video = store.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return VideoResponse.model_validate(video)

    @app.patch("/videos/{video_id}", response_model=VideoResponse)
    def update_video(
        video_id: int,
        payload: VideoUpdate,
        store: VideoStore = Depends(get_store),
    ) -> VideoResponse:
        """Update a video."""
        video = store.update_video(video_id, **payload.model_dump(exclude_unset=True))
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return VideoResponse.model_validate(video)

    @app.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_video(
        video_id: int,
        store: VideoStore = Depends(get_store),
    ) -> None:
        """Delete a video."""
        success = store.delete_video(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")

    @app.post("/videos/{video_id}/view", status_code=status.HTTP_204_NO_CONTENT)
    def record_view(
        video_id: int,
        store: VideoStore = Depends(get_store),
    ) -> None:
        """Record a video view."""
        store.increment_view_count(video_id)

    # ===== PLAYLIST ENDPOINTS =====

    @app.post("/playlists", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
    def create_playlist(
        payload: PlaylistCreate,
        user_id: Optional[int] = None,  # TODO: Get from auth token
        store: VideoStore = Depends(get_store),
    ) -> PlaylistResponse:
        """Create a new playlist."""
        playlist = store.create_playlist(
            name=payload.name,
            user_id=user_id,
            description=payload.description,
        )
        video_count = store.get_playlist_video_count(playlist.id)
        response = PlaylistResponse.model_validate(playlist)
        response.video_count = video_count
        return response

    @app.get("/playlists", response_model=list[PlaylistResponse])
    def list_playlists(
        user_id: Optional[int] = None,  # TODO: Get from auth token
        official_only: bool = False,
        store: VideoStore = Depends(get_store),
    ) -> list[PlaylistResponse]:
        """List playlists."""
        playlists = store.list_playlists(user_id=user_id, official_only=official_only)
        responses = []
        for playlist in playlists:
            video_count = store.get_playlist_video_count(playlist.id)
            response = PlaylistResponse.model_validate(playlist)
            response.video_count = video_count
            responses.append(response)
        return responses

    @app.get("/playlists/{playlist_id}", response_model=PlaylistResponse)
    def get_playlist(
        playlist_id: int,
        store: VideoStore = Depends(get_store),
    ) -> PlaylistResponse:
        """Get a specific playlist."""
        playlist = store.get_playlist(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        video_count = store.get_playlist_video_count(playlist.id)
        response = PlaylistResponse.model_validate(playlist)
        response.video_count = video_count
        return response

    @app.patch("/playlists/{playlist_id}", response_model=PlaylistResponse)
    def update_playlist(
        playlist_id: int,
        payload: PlaylistUpdate,
        store: VideoStore = Depends(get_store),
    ) -> PlaylistResponse:
        """Update a playlist."""
        playlist = store.get_playlist(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        if payload.name:
            playlist.name = payload.name
        if payload.description is not None:
            playlist.description = payload.description

        # Note: In a real app, we'd update via store method
        video_count = store.get_playlist_video_count(playlist.id)
        response = PlaylistResponse.model_validate(playlist)
        response.video_count = video_count
        return response

    @app.delete("/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_playlist(
        playlist_id: int,
        store: VideoStore = Depends(get_store),
    ) -> None:
        """Delete a playlist."""
        success = store.delete_playlist(playlist_id)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")

    @app.post("/playlists/{playlist_id}/videos", status_code=status.HTTP_201_CREATED)
    def add_video_to_playlist(
        playlist_id: int,
        payload: PlaylistAddVideo,
        store: VideoStore = Depends(get_store),
    ) -> dict:
        """Add a video to a playlist."""
        # Verify playlist and video exist
        playlist = store.get_playlist(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        video = store.get_video(payload.video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        store.add_video_to_playlist(playlist_id, payload.video_id)
        return {"message": "Video added to playlist"}

    @app.get("/playlists/{playlist_id}/videos", response_model=list[VideoResponse])
    def get_playlist_videos(
        playlist_id: int,
        store: VideoStore = Depends(get_store),
    ) -> list[VideoResponse]:
        """Get all videos in a playlist."""
        videos = store.get_playlist_videos(playlist_id)
        return [VideoResponse.model_validate(v) for v in videos]

    @app.delete("/playlists/{playlist_id}/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
    def remove_video_from_playlist(
        playlist_id: int,
        video_id: int,
        store: VideoStore = Depends(get_store),
    ) -> None:
        """Remove a video from a playlist."""
        success = store.remove_video_from_playlist(playlist_id, video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Video not in playlist")

    # ===== PROGRESS ENDPOINTS =====

    @app.post("/progress", response_model=VideoProgressResponse)
    def update_progress(
        payload: VideoProgressUpdate,
        user_id: int = 1,  # TODO: Get from auth token
        video_id: int = 1,  # TODO: Get from request body
        store: VideoStore = Depends(get_store),
    ) -> VideoProgressResponse:
        """Update video progress."""
        progress = store.update_progress(
            user_id=user_id,
            video_id=video_id,
            progress_seconds=payload.progress_seconds,
            completed=payload.completed,
        )
        return VideoProgressResponse.model_validate(progress)

    @app.get("/progress/{video_id}", response_model=VideoProgressResponse)
    def get_progress(
        video_id: int,
        user_id: int = 1,  # TODO: Get from auth token
        store: VideoStore = Depends(get_store),
    ) -> VideoProgressResponse:
        """Get video progress."""
        progress = store.get_progress(user_id, video_id)
        if not progress:
            raise HTTPException(status_code=404, detail="No progress found")
        return VideoProgressResponse.model_validate(progress)

    # ===== BOOKMARK ENDPOINTS =====

    @app.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
    def create_bookmark(
        payload: BookmarkCreate,
        user_id: int = 1,  # TODO: Get from auth token
        store: VideoStore = Depends(get_store),
    ) -> BookmarkResponse:
        """Create a video bookmark."""
        bookmark = store.create_bookmark(
            user_id=user_id,
            video_id=payload.video_id,
            timestamp_seconds=payload.timestamp_seconds,
            note=payload.note,
        )
        return BookmarkResponse.model_validate(bookmark)

    @app.get("/videos/{video_id}/bookmarks", response_model=list[BookmarkResponse])
    def get_bookmarks(
        video_id: int,
        user_id: int = 1,  # TODO: Get from auth token
        store: VideoStore = Depends(get_store),
    ) -> list[BookmarkResponse]:
        """Get all bookmarks for a video."""
        bookmarks = store.get_bookmarks(user_id, video_id)
        return [BookmarkResponse.model_validate(b) for b in bookmarks]

    @app.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_bookmark(
        bookmark_id: int,
        user_id: int = 1,  # TODO: Get from auth token
        store: VideoStore = Depends(get_store),
    ) -> None:
        """Delete a bookmark."""
        success = store.delete_bookmark(bookmark_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Bookmark not found")

    return app


# For running standalone
if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8007)
