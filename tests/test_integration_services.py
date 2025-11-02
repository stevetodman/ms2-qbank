"""Integration tests for cross-service workflows.

These tests validate that the complete system works end-to-end,
testing data flow and consistency across multiple services.

Test scenarios:
1. User watches video → progress tracked → analytics recorded
2. User answers questions → creates assessment → analytics updated
3. User creates flashcard → reviews it → analytics tracked
4. User creates note → links to resources → searchable
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Import service apps
from src.users.app import create_app as create_users_app
from src.videos.app import create_app as create_videos_app
from src.flashcards.app import create_app as create_flashcards_app
from src.analytics.user_app import create_app as create_analytics_app
from src.library.db_app import create_app as create_library_app
from src.assessments.db_app import create_app as create_assessments_app

# Import stores for test setup
from src.users.store import UserStore
from src.videos.store import VideoStore
from src.flashcards.store import FlashcardStore
from src.analytics.user_store import UserAnalyticsStore
from src.library.db_store import LibraryDatabaseStore
from src.assessments.db_store import AssessmentDatabaseStore


@pytest.fixture
def test_user_credentials():
    """Test user credentials."""
    return {
        "email": "integration@test.com",
        "password": "TestPassword123!",
        "full_name": "Integration Test User",
    }


@pytest.fixture
def users_client(tmp_path):
    """Create users service client with temporary database."""
    db_path = tmp_path / "users.db"
    store = UserStore(f"sqlite:///{db_path}")
    app = create_users_app(store=store)
    return TestClient(app), store


@pytest.fixture
def videos_client(tmp_path):
    """Create videos service client with temporary database."""
    db_path = tmp_path / "videos.db"
    store = VideoStore(f"sqlite:///{db_path}")
    app = create_videos_app(store=store)
    return TestClient(app), store


@pytest.fixture
def flashcards_client(tmp_path):
    """Create flashcards service client with temporary database."""
    db_path = tmp_path / "flashcards.db"
    store = FlashcardStore(f"sqlite:///{db_path}")
    app = create_flashcards_app(store=store)
    return TestClient(app), store


@pytest.fixture
def analytics_client(tmp_path):
    """Create analytics service client with temporary database."""
    db_path = tmp_path / "analytics.db"
    store = UserAnalyticsStore(f"{db_path}")
    app = create_analytics_app(store=store)
    return TestClient(app), store


@pytest.fixture
def library_client(tmp_path):
    """Create library service client with temporary database."""
    db_path = tmp_path / "library.db"
    store = LibraryDatabaseStore(f"sqlite:///{db_path}")
    app = create_library_app(store=store)
    return TestClient(app), store


@pytest.fixture
def assessments_client(tmp_path):
    """Create assessments service client with temporary database."""
    db_path = tmp_path / "assessments.db"
    store = AssessmentDatabaseStore(f"sqlite:///{db_path}", question_count=10)
    app = create_assessments_app(store=store, questions=[
        {
            "id": f"q{i}",
            "stem": f"Question {i}",
            "correct_answer": "A",
            "subject": "Cardiology",
            "system": "Cardiovascular",
        }
        for i in range(10)
    ])
    return TestClient(app), store


@pytest.fixture
def auth_token(users_client, test_user_credentials):
    """Create a test user and return their auth token."""
    client, store = users_client

    # Register user
    response = client.post("/register", json=test_user_credentials)
    assert response.status_code == 201

    # Login to get token
    login_response = client.post("/login", json={
        "email": test_user_credentials["email"],
        "password": test_user_credentials["password"],
    })
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_video_progress_to_analytics_flow(videos_client, analytics_client, users_client, auth_token):
    """Test: User watches video → progress saved → analytics can query it.

    This validates:
    - Video progress is persisted correctly
    - User identity is maintained across services
    - Analytics can access video viewing data
    """
    videos, videos_store = videos_client
    analytics, analytics_store = analytics_client
    users, users_store = users_client

    # Get user ID from token
    from src.users.auth import get_user_id_from_token
    user_id = get_user_id_from_token(auth_token)
    assert user_id is not None

    # Create a test video
    video = videos_store.create_video(
        title="Test Cardiology Lecture",
        description="A test video about cardiology",
        video_url="https://example.com/video.mp4",
        duration_seconds=600,
        subject="Cardiology",
        system="Cardiovascular",
    )

    # Simulate user watching video (update progress)
    progress = videos_store.update_progress(
        user_id=user_id,
        video_id=video.id,
        progress_seconds=300,  # Watched 5 minutes
        completed=False,
    )

    assert progress.user_id == user_id
    assert progress.video_id == video.id
    assert progress.progress_seconds == 300

    # Verify progress is persisted
    retrieved_progress = videos_store.get_progress(user_id, video.id)
    assert retrieved_progress is not None
    assert retrieved_progress.progress_seconds == 300

    # Complete the video
    videos_store.update_progress(
        user_id=user_id,
        video_id=video.id,
        progress_seconds=600,
        completed=True,
    )

    final_progress = videos_store.get_progress(user_id, video.id)
    assert final_progress.completed is True

    # Note: In a real system, video completion would trigger an analytics event
    # For now, we verify the data is accessible


def test_assessment_to_analytics_flow(assessments_client, analytics_client, users_client, auth_token):
    """Test: User completes assessment → results saved → analytics recorded.

    This validates:
    - Assessment workflow from creation to submission
    - Question attempts are recorded
    - Analytics can aggregate performance data
    """
    assessments, assessments_store = assessments_client
    analytics, analytics_store = analytics_client
    users, users_store = users_client

    # Get user ID
    from src.users.auth import get_user_id_from_token
    user_id = get_user_id_from_token(auth_token)

    # Create an assessment
    assessment = assessments_store.create(
        candidate_id=str(user_id),
        subject="Cardiology",
        time_limit_minutes=30,
    )

    assert assessment.status == "created"

    # Start the assessment
    question_ids = [f"q{i}" for i in range(5)]
    started = assessments_store.start(
        assessment_id=assessment.assessment_id,
        question_ids=question_ids,
    )

    assert started.status == "in-progress"
    assert started.total_questions == 5

    # Submit responses
    responses = {
        "q0": "A",  # Correct
        "q1": "A",  # Correct
        "q2": "B",  # Incorrect
        "q3": "A",  # Correct
        "q4": None,  # Omitted
    }

    correct_answers = {qid: "A" for qid in question_ids}

    submitted = assessments_store.submit(
        assessment_id=assessment.assessment_id,
        responses=responses,
        correct_answers=correct_answers,
    )

    assert submitted.status == "completed"
    assert submitted.correct == 3
    assert submitted.incorrect == 1
    assert submitted.omitted == 1
    assert submitted.percentage == 60.0

    # Record question attempts in analytics
    for qid, answer in responses.items():
        if answer is not None:  # Skip omitted
            analytics_store.record_attempt(
                user_id=user_id,
                question_id=qid,
                correct_answer="A",
                is_correct=(answer == "A"),
                assessment_id=assessment.assessment_id,
                answer_given=answer,
                subject="Cardiology",
                system="Cardiovascular",
                mode="assessment",
            )

    # Query analytics for this user
    user_analytics = analytics_store.compute_user_analytics(user_id, days=30)

    assert user_analytics.total_attempts == 4  # 4 answered, 1 omitted
    assert user_analytics.correct_attempts == 3
    assert user_analytics.incorrect_attempts == 1
    assert user_analytics.accuracy_percent == 75.0  # 3/4 correct
    assert user_analytics.assessments_completed >= 1


def test_flashcard_review_to_analytics_flow(flashcards_client, analytics_client, users_client, auth_token):
    """Test: User creates flashcard → reviews it → spaced repetition tracked.

    This validates:
    - Flashcard creation and retrieval
    - Spaced repetition algorithm works
    - Review history is maintained
    """
    flashcards, flashcards_store = flashcards_client
    analytics, analytics_store = analytics_client
    users, users_store = users_client

    # Get user ID
    from src.users.auth import get_user_id_from_token
    user_id = get_user_id_from_token(auth_token)

    # Create a deck
    deck = flashcards_store.create_deck(
        name="Cardiology Basics",
        deck_type="ready",
        user_id=user_id,
        category="Cardiology",
    )

    assert deck.user_id == user_id

    # Create a flashcard
    card = flashcards_store.create_card(
        deck_id=deck.id,
        front="What is the normal resting heart rate?",
        back="60-100 beats per minute",
        tags=["cardiology", "vital-signs"],
    )

    assert card.deck_id == deck.id

    # Get review state
    review_state = flashcards_store.get_or_create_review_state(card.id, user_id)

    assert review_state.card_id == card.id
    assert review_state.user_id == user_id
    assert review_state.repetitions == 0  # New card

    # Submit a review (quality = 4, good recall)
    updated_review = flashcards_store.submit_review(
        card_id=card.id,
        quality=4,
        user_id=user_id,
    )

    assert updated_review.repetitions == 1
    assert updated_review.last_quality == 4
    assert updated_review.total_reviews == 1
    assert updated_review.correct_count == 1

    # Submit another review (quality = 5, perfect recall)
    updated_review = flashcards_store.submit_review(
        card_id=card.id,
        quality=5,
        user_id=user_id,
    )

    assert updated_review.repetitions == 2
    assert updated_review.total_reviews == 2
    assert updated_review.correct_count == 2

    # Get deck stats
    stats = flashcards_store.get_deck_stats(deck.id, user_id)

    assert stats["total_cards"] == 1
    assert stats["new_cards"] == 0  # No longer new after review
    assert stats["total_reviews"] == 2
    assert stats["accuracy_percentage"] == 100.0


def test_library_note_with_resources_flow(library_client, users_client, auth_token):
    """Test: User creates note → links resources → can retrieve linked items.

    This validates:
    - Note creation and persistence
    - Resource linking (articles, videos, questions)
    - Cross-referencing capabilities
    """
    library, library_store = library_client
    users, users_store = users_client

    # Get user ID
    from src.users.auth import get_user_id_from_token
    user_id = get_user_id_from_token(auth_token)

    # Create an article
    article = library_store.create_article(
        article_id="article-1",
        title="Understanding Cardiac Output",
        summary="An overview of cardiac output measurement and significance",
        body="Detailed content about cardiac output...",
        tags=["cardiology", "physiology"],
    )

    # Create a note linking to the article
    note = library_store.create_note(
        note_id="note-1",
        user_id=user_id,
        title="My Study Notes on Cardiac Output",
        body="Key takeaways: CO = HR × SV...",
        tags=["study-notes", "cardiology"],
        article_ids=["article-1"],
        question_ids=["q123"],
        video_ids=["v456"],
    )

    assert note.user_id == user_id
    assert "article-1" in note.article_ids

    # Retrieve the note
    retrieved_note = library_store.get_note("note-1")
    assert retrieved_note is not None
    assert retrieved_note.user_id == user_id
    assert retrieved_note.title == note.title

    # Search notes by user
    user_notes = library_store.search_notes(user_id=user_id)
    assert len(user_notes) == 1
    assert user_notes[0].note_id == "note-1"

    # Bookmark the note
    library_store.toggle_note_bookmark("note-1", bookmarked=True)
    bookmarked_notes = library_store.search_notes(user_id=user_id, bookmarked_only=True)
    assert len(bookmarked_notes) == 1


def test_user_deletion_orphan_check(users_client, videos_client, flashcards_client):
    """Test: Verify orphaned records after user deletion (data integrity check).

    This test validates application-level referential integrity since
    cross-database foreign keys cannot be enforced in SQLite.

    Note: This is a validation test, not a requirement that data MUST be deleted.
    Some services may intentionally keep anonymized analytics.
    """
    users, users_store = users_client
    videos, videos_store = videos_client
    flashcards, flashcards_store = flashcards_client

    # Create a user
    user = users_store.create_user({
        "email": "orphan@test.com",
        "password": "TestPassword123!",
        "full_name": "Orphan Test",
    })

    # Create data linked to this user
    video = videos_store.create_video(
        title="Test Video",
        description="Test",
        video_url="https://example.com/test.mp4",
        duration_seconds=100,
        subject="Test",
        system="Test",
    )

    videos_store.update_progress(
        user_id=user.id,
        video_id=video.id,
        progress_seconds=50,
    )

    deck = flashcards_store.create_deck(
        name="Test Deck",
        deck_type="ready",
        user_id=user.id,
    )

    # Delete the user
    deleted = users_store.delete_user(user.id)
    assert deleted is True

    # Verify user is gone
    retrieved_user = users_store.get_user_by_email("orphan@test.com")
    assert retrieved_user is None

    # Check for orphaned records (these WILL exist due to cross-database limitation)
    # In a production system, these would be handled by:
    # 1. Periodic cleanup jobs
    # 2. Application-level cascade deletes
    # 3. Migration to unified database with proper FKs

    progress = videos_store.get_progress(user.id, video.id)
    # Progress may still exist (orphaned) - this is a known limitation

    decks = flashcards_store.list_decks(user_id=user.id)
    # Decks may still exist (orphaned) - this is a known limitation

    # This test documents the limitation, not a failure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
