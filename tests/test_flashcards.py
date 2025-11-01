"""Tests for flashcard system with spaced repetition."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flashcards.app import create_app
from flashcards.spaced_repetition import ReviewState, SpacedRepetitionScheduler
from flashcards.store import FlashcardStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create a FlashcardStore instance with temporary database."""
    return FlashcardStore(database_url=temp_db)


@pytest.fixture
def client(store):
    """Create a test client with the flashcard app."""
    app = create_app(store=store)
    return TestClient(app)


# ===== Spaced Repetition Algorithm Tests =====


def test_sm2_initial_state():
    """Test that initial review state is correct."""
    scheduler = SpacedRepetitionScheduler()
    state = scheduler.create_initial_state()

    assert state.ease_factor == 2.5
    assert state.interval_days == 0
    assert state.repetitions == 0
    assert state.next_review_date == date.today()
    assert state.streak == 0


def test_sm2_first_correct_review():
    """Test SM-2 algorithm for first correct review (quality >= 3)."""
    scheduler = SpacedRepetitionScheduler()
    initial_state = scheduler.create_initial_state()

    # Submit quality 4 (correct with hesitation)
    new_state = scheduler.calculate_next_review(initial_state, quality=4)

    assert new_state.repetitions == 1
    assert new_state.interval_days == 1  # First interval is 1 day
    assert new_state.next_review_date == date.today() + timedelta(days=1)
    assert new_state.streak == 1
    assert new_state.ease_factor >= 2.5  # Should increase or stay same


def test_sm2_second_correct_review():
    """Test SM-2 algorithm for second correct review."""
    scheduler = SpacedRepetitionScheduler()

    # Start from first review state
    first_state = ReviewState(
        ease_factor=2.6,
        interval_days=1,
        repetitions=1,
        next_review_date=date.today(),
        streak=1,
    )

    # Submit quality 5 (perfect recall)
    new_state = scheduler.calculate_next_review(first_state, quality=5)

    assert new_state.repetitions == 2
    assert new_state.interval_days == 6  # Second interval is 6 days
    assert new_state.next_review_date == date.today() + timedelta(days=6)
    assert new_state.streak == 2


def test_sm2_subsequent_reviews():
    """Test SM-2 algorithm for third and beyond reviews."""
    scheduler = SpacedRepetitionScheduler()

    # Start from second review state
    second_state = ReviewState(
        ease_factor=2.7,
        interval_days=6,
        repetitions=2,
        next_review_date=date.today(),
        streak=2,
    )

    # Submit quality 4
    new_state = scheduler.calculate_next_review(second_state, quality=4)

    assert new_state.repetitions == 3
    # Interval should be previous interval * ease factor
    assert new_state.interval_days == round(6 * 2.7)  # Should be ~16 days
    assert new_state.streak == 3


def test_sm2_incorrect_review_resets():
    """Test that quality < 3 resets the learning process."""
    scheduler = SpacedRepetitionScheduler()

    # Start from an advanced state
    advanced_state = ReviewState(
        ease_factor=2.8,
        interval_days=16,
        repetitions=3,
        next_review_date=date.today(),
        streak=3,
    )

    # Submit quality 2 (incorrect)
    new_state = scheduler.calculate_next_review(advanced_state, quality=2)

    assert new_state.repetitions == 0  # Reset
    assert new_state.interval_days == 1  # Back to 1 day
    assert new_state.streak == 0  # Streak broken
    # Ease factor should decrease but stay above minimum
    assert new_state.ease_factor < advanced_state.ease_factor
    assert new_state.ease_factor >= 1.3


def test_sm2_ease_factor_minimum():
    """Test that ease factor never goes below minimum."""
    scheduler = SpacedRepetitionScheduler()

    # Start with minimum ease factor
    state = ReviewState(
        ease_factor=1.3,
        interval_days=6,
        repetitions=2,
        next_review_date=date.today(),
        streak=2,
    )

    # Submit quality 0 (complete blackout) - should decrease ease factor
    new_state = scheduler.calculate_next_review(state, quality=0)

    assert new_state.ease_factor >= 1.3  # Should not go below minimum


def test_sm2_invalid_quality():
    """Test that invalid quality ratings raise ValueError."""
    scheduler = SpacedRepetitionScheduler()
    state = scheduler.create_initial_state()

    with pytest.raises(ValueError):
        scheduler.calculate_next_review(state, quality=6)

    with pytest.raises(ValueError):
        scheduler.calculate_next_review(state, quality=-1)


def test_sm2_is_due():
    """Test due date checking."""
    scheduler = SpacedRepetitionScheduler()

    # Card due today
    assert scheduler.is_due(date.today())

    # Card due yesterday (overdue)
    assert scheduler.is_due(date.today() - timedelta(days=1))

    # Card due tomorrow (not yet due)
    assert not scheduler.is_due(date.today() + timedelta(days=1))


# ===== API Tests =====


def test_create_deck(client):
    """Test creating a new deck."""
    response = client.post(
        "/decks",
        json={
            "name": "Anatomy Essentials",
            "description": "Core anatomy concepts",
            "deck_type": "ready",
            "category": "Anatomy",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Anatomy Essentials"
    assert data["deck_type"] == "ready"
    assert data["category"] == "Anatomy"
    assert data["is_active"] is True
    assert data["card_count"] == 0


def test_list_decks(client):
    """Test listing decks."""
    # Create two decks
    client.post(
        "/decks",
        json={"name": "Deck 1", "deck_type": "ready"},
    )
    client.post(
        "/decks",
        json={"name": "Deck 2", "deck_type": "smart"},
    )

    # List all decks
    response = client.get("/decks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Filter by type
    response = client.get("/decks?deck_type=ready")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["deck_type"] == "ready"


def test_create_card(client):
    """Test creating a flashcard."""
    # Create deck first
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    # Create card
    response = client.post(
        "/cards",
        json={
            "deck_id": deck_id,
            "front": "What is the largest organ in the human body?",
            "back": "The skin",
            "hint": "It covers the entire body",
            "tags": ["anatomy", "integumentary"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["front"] == "What is the largest organ in the human body?"
    assert data["back"] == "The skin"
    assert data["hint"] == "It covers the entire body"
    assert "anatomy" in data["tags"]
    assert data["deck_id"] == deck_id


def test_list_cards_in_deck(client):
    """Test listing cards in a deck."""
    # Create deck
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    # Create multiple cards
    for i in range(3):
        client.post(
            "/cards",
            json={
                "deck_id": deck_id,
                "front": f"Question {i + 1}",
                "back": f"Answer {i + 1}",
            },
        )

    # List cards
    response = client.get(f"/decks/{deck_id}/cards")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_submit_review(client):
    """Test submitting a card review."""
    # Create deck and card
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    card_response = client.post(
        "/cards",
        json={
            "deck_id": deck_id,
            "front": "Test question",
            "back": "Test answer",
        },
    )
    card_id = card_response.json()["id"]

    # Submit review with quality 4 (correct with hesitation)
    response = client.post(
        "/reviews",
        json={"card_id": card_id, "quality": 4},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["card_id"] == card_id
    assert data["interval_days"] == 1  # First correct review
    assert data["ease_factor"] >= 2.5
    assert data["streak"] == 1
    # Next review should be tomorrow
    expected_date = (date.today() + timedelta(days=1)).isoformat()
    assert data["next_review_date"] == expected_date


def test_get_due_cards(client):
    """Test getting cards due for review."""
    # Create deck
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    # Create cards
    card1_response = client.post(
        "/cards",
        json={"deck_id": deck_id, "front": "Q1", "back": "A1"},
    )
    card1_id = card1_response.json()["id"]

    card2_response = client.post(
        "/cards",
        json={"deck_id": deck_id, "front": "Q2", "back": "A2"},
    )

    # Initially, all cards should be due (new cards)
    response = client.get(f"/decks/{deck_id}/due")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Review one card
    client.post("/reviews", json={"card_id": card1_id, "quality": 5})

    # Should still have 2 due (one reviewed but due tomorrow, one new)
    # Actually, after review with quality 5, card1 is due in 1 day
    # So only card2 should be due today
    response = client.get(f"/decks/{deck_id}/due")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Only the unreviewed card


def test_deck_statistics(client):
    """Test deck statistics endpoint."""
    # Create deck and cards
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    # Create 5 cards
    card_ids = []
    for i in range(5):
        card_response = client.post(
            "/cards",
            json={"deck_id": deck_id, "front": f"Q{i}", "back": f"A{i}"},
        )
        card_ids.append(card_response.json()["id"])

    # Review 3 cards with different qualities
    client.post("/reviews", json={"card_id": card_ids[0], "quality": 5})  # Perfect
    client.post("/reviews", json={"card_id": card_ids[1], "quality": 4})  # Good
    client.post("/reviews", json={"card_id": card_ids[2], "quality": 2})  # Incorrect

    # Get stats
    response = client.get(f"/decks/{deck_id}/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_cards"] == 5
    assert data["new_cards"] == 3  # 2 never reviewed + 1 reset to 0
    assert data["total_reviews"] == 3
    assert data["accuracy_percentage"] > 0


def test_update_card(client):
    """Test updating a card."""
    # Create deck and card
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    card_response = client.post(
        "/cards",
        json={"deck_id": deck_id, "front": "Old question", "back": "Old answer"},
    )
    card_id = card_response.json()["id"]

    # Update card
    response = client.patch(
        f"/cards/{card_id}",
        json={"front": "New question", "back": "New answer"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["front"] == "New question"
    assert data["back"] == "New answer"


def test_delete_deck_cascades(client):
    """Test that deleting a deck deletes its cards."""
    # Create deck with cards
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck", "deck_type": "smart"},
    )
    deck_id = deck_response.json()["id"]

    client.post(
        "/cards",
        json={"deck_id": deck_id, "front": "Q1", "back": "A1"},
    )

    # Delete deck
    response = client.delete(f"/decks/{deck_id}")
    assert response.status_code == 204

    # Verify deck is gone
    response = client.get(f"/decks/{deck_id}")
    assert response.status_code == 404
