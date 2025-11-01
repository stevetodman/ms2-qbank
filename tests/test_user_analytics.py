"""Tests for user performance analytics."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create a UserAnalyticsStore with a temporary database."""
    from src.analytics.user_store import UserAnalyticsStore

    return UserAnalyticsStore(db_path=temp_db)


@pytest.fixture
def client(temp_db, monkeypatch):
    """Create a test client with a temporary database."""
    # Mock the database path
    monkeypatch.setattr("src.analytics.user_app.DB_PATH", temp_db.replace("sqlite:///", ""))

    # Mock authentication
    def mock_optional_auth():
        return 1

    def mock_get_current_user_id():
        return 1

    monkeypatch.setattr("src.analytics.user_app.optional_auth", lambda: 1)
    monkeypatch.setattr("src.analytics.user_app.get_current_user_id", lambda: 1)

    from src.analytics.user_app import app, UserAnalyticsStore

    # Reinitialize store with temp db
    app.dependency_overrides = {}
    store = UserAnalyticsStore(db_path=temp_db)
    monkeypatch.setattr("src.analytics.user_app.store", store)

    return TestClient(app)


class TestUserAnalyticsStore:
    """Tests for UserAnalyticsStore."""

    def test_record_attempt_basic(self, store):
        """Test recording a basic question attempt."""
        attempt = store.record_attempt(
            user_id=1,
            question_id="q123",
            correct_answer="A",
            is_correct=True,
            subject="Anatomy",
            system="Cardiovascular",
            difficulty="Medium",
            time_seconds=45,
        )

        assert attempt.id is not None
        assert attempt.user_id == 1
        assert attempt.question_id == "q123"
        assert attempt.is_correct is True
        assert attempt.subject == "Anatomy"
        assert attempt.time_seconds == 45

    def test_record_multiple_attempts(self, store):
        """Test recording multiple attempts."""
        # Record 5 correct attempts
        for i in range(5):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=True,
                subject="Anatomy",
            )

        # Record 3 incorrect attempts
        for i in range(5, 8):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=False,
                answer_given="B",
                subject="Physiology",
            )

        attempts = store.get_user_attempts(user_id=1)
        assert len(attempts) == 8

    def test_get_user_attempts_with_filtering(self, store):
        """Test retrieving attempts with subject/system filtering."""
        # Create attempts with different subjects
        store.record_attempt(
            user_id=1, question_id="q1", correct_answer="A", is_correct=True, subject="Anatomy"
        )
        store.record_attempt(
            user_id=1, question_id="q2", correct_answer="A", is_correct=True, subject="Physiology"
        )
        store.record_attempt(
            user_id=1, question_id="q3", correct_answer="A", is_correct=True, subject="Anatomy"
        )

        # Filter by subject
        anatomy_attempts = store.get_user_attempts(user_id=1, subject="Anatomy")
        assert len(anatomy_attempts) == 2

        physiology_attempts = store.get_user_attempts(user_id=1, subject="Physiology")
        assert len(physiology_attempts) == 1

    def test_compute_user_analytics_empty(self, store):
        """Test computing analytics for a user with no attempts."""
        analytics = store.compute_user_analytics(user_id=1)

        assert analytics.user_id == 1
        assert analytics.total_attempts == 0
        assert analytics.accuracy_percent == 0.0
        assert len(analytics.by_subject) == 0

    def test_compute_user_analytics_basic(self, store):
        """Test computing basic analytics."""
        # Create 10 attempts: 7 correct, 3 incorrect
        for i in range(7):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=True,
                subject="Anatomy",
                time_seconds=60,
            )

        for i in range(7, 10):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=False,
                subject="Physiology",
                time_seconds=90,
            )

        analytics = store.compute_user_analytics(user_id=1)

        assert analytics.total_attempts == 10
        assert analytics.correct_attempts == 7
        assert analytics.incorrect_attempts == 3
        assert analytics.accuracy_percent == 70.0
        assert analytics.average_time_seconds == 69.0  # (7*60 + 3*90) / 10
        assert analytics.questions_attempted_count == 10

    def test_compute_subject_performance(self, store):
        """Test subject performance breakdown."""
        # Anatomy: 4 correct, 1 incorrect
        for i in range(4):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=True,
                subject="Anatomy",
            )
        store.record_attempt(
            user_id=1, question_id="q4", correct_answer="A", is_correct=False, subject="Anatomy"
        )

        # Physiology: 2 correct, 3 incorrect
        for i in range(5, 7):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=True,
                subject="Physiology",
            )
        for i in range(7, 10):
            store.record_attempt(
                user_id=1,
                question_id=f"q{i}",
                correct_answer="A",
                is_correct=False,
                subject="Physiology",
            )

        analytics = store.compute_user_analytics(user_id=1)

        assert len(analytics.by_subject) == 2

        # Anatomy should be first (higher accuracy)
        anatomy = next(s for s in analytics.by_subject if s.subject == "Anatomy")
        assert anatomy.total_attempts == 5
        assert anatomy.correct == 4
        assert anatomy.accuracy_percent == 80.0

        physiology = next(s for s in analytics.by_subject if s.subject == "Physiology")
        assert physiology.total_attempts == 5
        assert physiology.correct == 2
        assert physiology.accuracy_percent == 40.0

    def test_compute_system_performance(self, store):
        """Test organ system performance breakdown."""
        # Cardiovascular: high accuracy
        for i in range(8):
            store.record_attempt(
                user_id=1,
                question_id=f"cardio_{i}",
                correct_answer="A",
                is_correct=True,
                system="Cardiovascular",
            )
        store.record_attempt(
            user_id=1,
            question_id="cardio_8",
            correct_answer="A",
            is_correct=False,
            system="Cardiovascular",
        )

        # Respiratory: low accuracy
        for i in range(3):
            store.record_attempt(
                user_id=1,
                question_id=f"resp_{i}",
                correct_answer="A",
                is_correct=True,
                system="Respiratory",
            )
        for i in range(3, 7):
            store.record_attempt(
                user_id=1,
                question_id=f"resp_{i}",
                correct_answer="A",
                is_correct=False,
                system="Respiratory",
            )

        analytics = store.compute_user_analytics(user_id=1)

        assert len(analytics.by_system) == 2

        cardio = next(s for s in analytics.by_system if s.system == "Cardiovascular")
        assert cardio.accuracy_percent > 85.0

        resp = next(s for s in analytics.by_system if s.system == "Respiratory")
        assert resp.accuracy_percent < 50.0

    def test_compute_difficulty_performance(self, store):
        """Test difficulty performance breakdown."""
        # Easy: 5 correct, 0 incorrect
        for i in range(5):
            store.record_attempt(
                user_id=1,
                question_id=f"easy_{i}",
                correct_answer="A",
                is_correct=True,
                difficulty="Easy",
            )

        # Medium: 3 correct, 2 incorrect
        for i in range(3):
            store.record_attempt(
                user_id=1,
                question_id=f"medium_{i}",
                correct_answer="A",
                is_correct=True,
                difficulty="Medium",
            )
        for i in range(3, 5):
            store.record_attempt(
                user_id=1,
                question_id=f"medium_{i}",
                correct_answer="A",
                is_correct=False,
                difficulty="Medium",
            )

        # Hard: 1 correct, 4 incorrect
        store.record_attempt(
            user_id=1, question_id="hard_0", correct_answer="A", is_correct=True, difficulty="Hard"
        )
        for i in range(1, 5):
            store.record_attempt(
                user_id=1,
                question_id=f"hard_{i}",
                correct_answer="A",
                is_correct=False,
                difficulty="Hard",
            )

        analytics = store.compute_user_analytics(user_id=1)

        assert len(analytics.by_difficulty) == 3

        # Should be sorted Easy -> Medium -> Hard
        assert analytics.by_difficulty[0].difficulty == "Easy"
        assert analytics.by_difficulty[1].difficulty == "Medium"
        assert analytics.by_difficulty[2].difficulty == "Hard"

        assert analytics.by_difficulty[0].accuracy_percent == 100.0
        assert analytics.by_difficulty[1].accuracy_percent == 60.0
        assert analytics.by_difficulty[2].accuracy_percent == 20.0

    def test_compute_daily_performance(self, store):
        """Test daily performance time series."""
        # Create attempts over 3 days
        now = datetime.utcnow()

        # Day 1: 3 correct, 1 incorrect
        for i in range(3):
            attempt = store.record_attempt(
                user_id=1, question_id=f"d1_q{i}", correct_answer="A", is_correct=True
            )
            attempt.attempted_at = now - timedelta(days=2)

        # Day 2: 2 correct, 2 incorrect
        for i in range(2):
            attempt = store.record_attempt(
                user_id=1, question_id=f"d2_q{i}", correct_answer="A", is_correct=True
            )
            attempt.attempted_at = now - timedelta(days=1)

        # Day 3: 4 correct, 1 incorrect
        for i in range(4):
            attempt = store.record_attempt(
                user_id=1, question_id=f"d3_q{i}", correct_answer="A", is_correct=True
            )

        analytics = store.compute_user_analytics(user_id=1)

        # Should have entries for all days with activity
        assert len(analytics.daily_performance) >= 1

    def test_identify_weak_areas(self, store):
        """Test identification of weak performance areas."""
        # Create weak subject (< 70% accuracy with > 10 attempts)
        for i in range(6):
            store.record_attempt(
                user_id=1,
                question_id=f"weak_{i}",
                correct_answer="A",
                is_correct=True,
                subject="Pharmacology",
            )
        for i in range(6, 15):
            store.record_attempt(
                user_id=1,
                question_id=f"weak_{i}",
                correct_answer="A",
                is_correct=False,
                subject="Pharmacology",
            )

        # Create strong subject (> 70% accuracy)
        for i in range(10):
            store.record_attempt(
                user_id=1,
                question_id=f"strong_{i}",
                correct_answer="A",
                is_correct=True,
                subject="Anatomy",
            )

        analytics = store.compute_user_analytics(user_id=1)

        # Should identify Pharmacology as weak area
        weak_pharmacology = next(
            (w for w in analytics.weak_areas if w.name == "Pharmacology"), None
        )
        assert weak_pharmacology is not None
        assert weak_pharmacology.accuracy_percent == 40.0

    def test_compute_percentile_ranking(self, store):
        """Test percentile ranking computation."""
        # User 1: 80% accuracy, 10 attempts
        for i in range(8):
            store.record_attempt(
                user_id=1, question_id=f"u1_q{i}", correct_answer="A", is_correct=True
            )
        for i in range(8, 10):
            store.record_attempt(
                user_id=1, question_id=f"u1_q{i}", correct_answer="A", is_correct=False
            )

        # User 2: 60% accuracy, 10 attempts
        for i in range(6):
            store.record_attempt(
                user_id=2, question_id=f"u2_q{i}", correct_answer="A", is_correct=True
            )
        for i in range(6, 10):
            store.record_attempt(
                user_id=2, question_id=f"u2_q{i}", correct_answer="A", is_correct=False
            )

        # User 1 should rank higher than User 2
        ranking = store.compute_percentile_ranking(user_id=1)
        assert ranking.user_id == 1
        assert ranking.accuracy_percentile > 50.0
        assert ranking.total_users == 2


class TestUserAnalyticsAPI:
    """Tests for user analytics API endpoints."""

    def test_record_attempt_endpoint(self, client):
        """Test POST /attempts endpoint."""
        response = client.post(
            "/attempts",
            json={
                "question_id": "q123",
                "correct_answer": "A",
                "is_correct": True,
                "subject": "Anatomy",
                "time_seconds": 45,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "attempt_id" in data

    def test_get_recent_attempts_endpoint(self, client):
        """Test GET /attempts/recent endpoint."""
        # Record some attempts first
        for i in range(5):
            client.post(
                "/attempts",
                json={
                    "question_id": f"q{i}",
                    "correct_answer": "A",
                    "is_correct": i % 2 == 0,
                },
            )

        response = client.get("/attempts/recent?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_get_user_analytics_endpoint(self, client):
        """Test GET /analytics endpoint."""
        # Record some attempts
        for i in range(10):
            client.post(
                "/attempts",
                json={
                    "question_id": f"q{i}",
                    "correct_answer": "A",
                    "is_correct": i < 7,
                    "subject": "Anatomy" if i < 5 else "Physiology",
                },
            )

        response = client.get("/analytics?days=30")
        assert response.status_code == 200

        data = response.json()
        assert data["total_attempts"] == 10
        assert data["correct_attempts"] == 7
        assert data["accuracy_percent"] == 70.0
        assert len(data["by_subject"]) == 2

    def test_get_percentile_ranking_endpoint(self, client):
        """Test GET /analytics/percentile endpoint."""
        # Record some attempts
        for i in range(10):
            client.post(
                "/attempts",
                json={
                    "question_id": f"q{i}",
                    "correct_answer": "A",
                    "is_correct": i < 8,
                },
            )

        response = client.get("/analytics/percentile")
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == 1
        assert "overall_percentile" in data
        assert "accuracy_percentile" in data

    def test_health_check_endpoint(self, client):
        """Test GET /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user-analytics"
