"""Tests for video library service."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.videos.app import create_app
from src.videos.store import VideoStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create a VideoStore instance with temporary database."""
    return VideoStore(database_url=temp_db)


@pytest.fixture
def client(store):
    """Create a test client."""
    app = create_app(store=store)
    return TestClient(app)


# ===== VIDEO TESTS =====


def test_create_video(client):
    """Test creating a video."""
    response = client.post(
        "/videos",
        json={
            "title": "Cardiac Cycle Explained",
            "description": "Detailed explanation of the cardiac cycle phases",
            "video_url": "https://example.com/videos/cardiac-cycle.mp4",
            "thumbnail_url": "https://example.com/thumbnails/cardiac-cycle.jpg",
            "duration_seconds": 600,
            "subject": "Physiology",
            "system": "Cardiovascular",
            "topic": "Cardiac Cycle",
            "instructor": "Dr. Smith",
            "difficulty": "Medium",
            "tags": "cardiology,physiology,high-yield",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Cardiac Cycle Explained"
    assert data["duration_seconds"] == 600
    assert data["subject"] == "Physiology"
    assert data["view_count"] == 0


def test_list_videos(client):
    """Test listing videos."""
    # Create test videos
    client.post(
        "/videos",
        json={
            "title": "Video 1",
            "description": "Test",
            "video_url": "http://example.com/1.mp4",
            "duration_seconds": 300,
            "subject": "Anatomy",
            "system": "Cardiovascular",
        },
    )
    client.post(
        "/videos",
        json={
            "title": "Video 2",
            "description": "Test",
            "video_url": "http://example.com/2.mp4",
            "duration_seconds": 400,
            "subject": "Physiology",
            "system": "Respiratory",
        },
    )

    # List all videos
    response = client.get("/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_filter_videos_by_subject(client):
    """Test filtering videos by subject."""
    # Create videos
    client.post(
        "/videos",
        json={
            "title": "Anatomy Video",
            "description": "Test",
            "video_url": "http://example.com/1.mp4",
            "duration_seconds": 300,
            "subject": "Anatomy",
            "system": "Cardiovascular",
        },
    )
    client.post(
        "/videos",
        json={
            "title": "Physiology Video",
            "description": "Test",
            "video_url": "http://example.com/2.mp4",
            "duration_seconds": 400,
            "subject": "Physiology",
            "system": "Respiratory",
        },
    )

    # Filter by subject
    response = client.get("/videos?subject=Anatomy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["subject"] == "Anatomy"


def test_get_video(client):
    """Test getting a specific video."""
    # Create a video
    create_response = client.post(
        "/videos",
        json={
            "title": "Test Video",
            "description": "Test description",
            "video_url": "http://example.com/test.mp4",
            "duration_seconds": 500,
            "subject": "Pathology",
            "system": "Respiratory",
        },
    )
    video_id = create_response.json()["id"]

    # Get the video
    response = client.get(f"/videos/{video_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["id"] == video_id


def test_update_video(client):
    """Test updating a video."""
    # Create a video
    create_response = client.post(
        "/videos",
        json={
            "title": "Original Title",
            "description": "Original description",
            "video_url": "http://example.com/video.mp4",
            "duration_seconds": 300,
            "subject": "Anatomy",
            "system": "Musculoskeletal",
        },
    )
    video_id = create_response.json()["id"]

    # Update the video
    response = client.patch(
        f"/videos/{video_id}",
        json={"title": "Updated Title", "difficulty": "Hard"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["difficulty"] == "Hard"
    assert data["description"] == "Original description"  # Unchanged


def test_delete_video(client):
    """Test deleting a video."""
    # Create a video
    create_response = client.post(
        "/videos",
        json={
            "title": "Video to Delete",
            "description": "Test",
            "video_url": "http://example.com/delete.mp4",
            "duration_seconds": 200,
            "subject": "Biochemistry",
            "system": "Multisystem",
        },
    )
    video_id = create_response.json()["id"]

    # Delete the video
    response = client.delete(f"/videos/{video_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/videos/{video_id}")
    assert response.status_code == 404


def test_record_view(client):
    """Test recording a video view."""
    # Create a video
    create_response = client.post(
        "/videos",
        json={
            "title": "Popular Video",
            "description": "Test",
            "video_url": "http://example.com/popular.mp4",
            "duration_seconds": 600,
            "subject": "Pharmacology",
            "system": "Cardiovascular",
        },
    )
    video_id = create_response.json()["id"]

    # Record views
    client.post(f"/videos/{video_id}/view")
    client.post(f"/videos/{video_id}/view")
    client.post(f"/videos/{video_id}/view")

    # Check view count
    response = client.get(f"/videos/{video_id}")
    data = response.json()
    assert data["view_count"] == 3


# ===== PLAYLIST TESTS =====


def test_create_playlist(client):
    """Test creating a playlist."""
    response = client.post(
        "/playlists",
        json={
            "name": "Cardiology Essentials",
            "description": "Must-watch cardiology videos",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cardiology Essentials"
    assert data["video_count"] == 0
    assert data["is_official"] == False


def test_add_video_to_playlist(client):
    """Test adding videos to a playlist."""
    # Create a playlist
    playlist_response = client.post(
        "/playlists",
        json={"name": "My Playlist", "description": "Test playlist"},
    )
    playlist_id = playlist_response.json()["id"]

    # Create a video
    video_response = client.post(
        "/videos",
        json={
            "title": "Test Video",
            "description": "Test",
            "video_url": "http://example.com/test.mp4",
            "duration_seconds": 300,
            "subject": "Anatomy",
            "system": "Nervous",
        },
    )
    video_id = video_response.json()["id"]

    # Add video to playlist
    response = client.post(
        f"/playlists/{playlist_id}/videos",
        json={"video_id": video_id},
    )
    assert response.status_code == 201


def test_get_playlist_videos(client):
    """Test getting videos from a playlist."""
    # Create playlist
    playlist_response = client.post(
        "/playlists",
        json={"name": "Test Playlist"},
    )
    playlist_id = playlist_response.json()["id"]

    # Create and add videos
    for i in range(3):
        video_response = client.post(
            "/videos",
            json={
                "title": f"Video {i}",
                "description": f"Test video {i}",
                "video_url": f"http://example.com/{i}.mp4",
                "duration_seconds": 300,
                "subject": "Anatomy",
                "system": "Cardiovascular",
            },
        )
        video_id = video_response.json()["id"]
        client.post(
            f"/playlists/{playlist_id}/videos",
            json={"video_id": video_id},
        )

    # Get playlist videos
    response = client.get(f"/playlists/{playlist_id}/videos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_remove_video_from_playlist(client):
    """Test removing a video from a playlist."""
    # Create playlist and video
    playlist_response = client.post("/playlists", json={"name": "Test"})
    playlist_id = playlist_response.json()["id"]

    video_response = client.post(
        "/videos",
        json={
            "title": "Test Video",
            "description": "Test",
            "video_url": "http://example.com/test.mp4",
            "duration_seconds": 300,
            "subject": "Anatomy",
            "system": "Cardiovascular",
        },
    )
    video_id = video_response.json()["id"]

    # Add video
    client.post(f"/playlists/{playlist_id}/videos", json={"video_id": video_id})

    # Remove video
    response = client.delete(f"/playlists/{playlist_id}/videos/{video_id}")
    assert response.status_code == 204

    # Verify it's removed
    response = client.get(f"/playlists/{playlist_id}/videos")
    data = response.json()
    assert len(data) == 0


def test_delete_playlist(client):
    """Test deleting a playlist."""
    # Create playlist
    create_response = client.post(
        "/playlists",
        json={"name": "Playlist to Delete"},
    )
    playlist_id = create_response.json()["id"]

    # Delete playlist
    response = client.delete(f"/playlists/{playlist_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/playlists/{playlist_id}")
    assert response.status_code == 404
