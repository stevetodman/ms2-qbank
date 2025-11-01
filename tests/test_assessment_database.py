"""Tests for database-backed assessment store."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create an AssessmentDatabaseStore with a temporary database."""
    from src.assessments.db_store import AssessmentDatabaseStore

    return AssessmentDatabaseStore(db_path=temp_db, question_count=10)


class TestAssessmentDatabaseStore:
    """Tests for AssessmentDatabaseStore."""

    def test_create_assessment(self, store):
        """Test creating a new assessment."""
        assessment = store.create(
            candidate_id="user123",
            subject="Anatomy",
            system="Cardiovascular",
            difficulty="Medium",
            tags=["cardiology", "step2"],
            time_limit_minutes=120,
        )

        assert assessment.id is not None
        assert assessment.assessment_id is not None
        assert assessment.candidate_id == "user123"
        assert assessment.subject == "Anatomy"
        assert assessment.system == "Cardiovascular"
        assert assessment.difficulty == "Medium"
        assert assessment.time_limit_minutes == 120
        assert assessment.status == "created"
        assert assessment.created_at is not None

    def test_get_assessment(self, store):
        """Test retrieving an assessment."""
        created = store.create(candidate_id="user123")
        retrieved = store.get(created.assessment_id)

        assert retrieved is not None
        assert retrieved.assessment_id == created.assessment_id
        assert retrieved.candidate_id == "user123"

    def test_get_nonexistent_assessment(self, store):
        """Test retrieving a non-existent assessment."""
        result = store.get("nonexistent")
        assert result is None

    def test_start_assessment(self, store):
        """Test starting an assessment."""
        assessment = store.create(candidate_id="user123", time_limit_minutes=60)
        question_ids = [f"q{i}" for i in range(10)]

        started = store.start(assessment.assessment_id, question_ids)

        assert started.status == "in-progress"
        assert started.started_at is not None
        assert started.expires_at is not None
        assert started.total_questions == 10
        import json
        assert json.loads(started.question_ids) == question_ids

    def test_start_assessment_calculates_expiration(self, store):
        """Test that starting an assessment calculates correct expiration."""
        assessment = store.create(candidate_id="user123", time_limit_minutes=30)
        question_ids = [f"q{i}" for i in range(5)]

        started = store.start(assessment.assessment_id, question_ids)

        assert started.expires_at is not None
        expected_duration = timedelta(minutes=30)
        actual_duration = started.expires_at - started.started_at
        # Allow 1 second tolerance for test execution time
        assert abs(actual_duration.total_seconds() - expected_duration.total_seconds()) < 1

    def test_start_assessment_with_no_time_limit(self, store):
        """Test starting an assessment with no time limit."""
        assessment = store.create(candidate_id="user123", time_limit_minutes=0)
        question_ids = [f"q{i}" for i in range(5)]

        started = store.start(assessment.assessment_id, question_ids)

        assert started.status == "in-progress"
        assert started.expires_at is None

    def test_submit_assessment(self, store):
        """Test submitting an assessment."""
        # Create and start assessment
        assessment = store.create(candidate_id="user123")
        question_ids = ["q1", "q2", "q3", "q4", "q5"]
        store.start(assessment.assessment_id, question_ids)

        # Submit responses
        responses = {
            "q1": "A",
            "q2": "B",
            "q3": "A",
            "q4": "C",
            "q5": None,  # Omitted
        }
        correct_answers = {
            "q1": "A",  # Correct
            "q2": "A",  # Incorrect
            "q3": "A",  # Correct
            "q4": "C",  # Correct
            "q5": "B",  # Omitted
        }

        submitted = store.submit(assessment.assessment_id, responses, correct_answers)

        assert submitted.status == "completed"
        assert submitted.submitted_at is not None
        assert submitted.total_questions == 5
        assert submitted.correct == 3
        assert submitted.incorrect == 1
        assert submitted.omitted == 1
        assert submitted.percentage == 60.0
        assert submitted.duration_seconds is not None

    def test_submit_perfect_score(self, store):
        """Test submitting an assessment with perfect score."""
        assessment = store.create(candidate_id="user123")
        question_ids = ["q1", "q2", "q3"]
        store.start(assessment.assessment_id, question_ids)

        responses = {"q1": "A", "q2": "B", "q3": "C"}
        correct_answers = {"q1": "A", "q2": "B", "q3": "C"}

        submitted = store.submit(assessment.assessment_id, responses, correct_answers)

        assert submitted.correct == 3
        assert submitted.incorrect == 0
        assert submitted.omitted == 0
        assert submitted.percentage == 100.0

    def test_submit_all_incorrect(self, store):
        """Test submitting an assessment with all incorrect answers."""
        assessment = store.create(candidate_id="user123")
        question_ids = ["q1", "q2", "q3"]
        store.start(assessment.assessment_id, question_ids)

        responses = {"q1": "B", "q2": "C", "q3": "D"}
        correct_answers = {"q1": "A", "q2": "B", "q3": "C"}

        submitted = store.submit(assessment.assessment_id, responses, correct_answers)

        assert submitted.correct == 0
        assert submitted.incorrect == 3
        assert submitted.omitted == 0
        assert submitted.percentage == 0.0

    def test_submit_all_omitted(self, store):
        """Test submitting an assessment with all omitted answers."""
        assessment = store.create(candidate_id="user123")
        question_ids = ["q1", "q2", "q3"]
        store.start(assessment.assessment_id, question_ids)

        responses = {}
        correct_answers = {"q1": "A", "q2": "B", "q3": "C"}

        submitted = store.submit(assessment.assessment_id, responses, correct_answers)

        assert submitted.correct == 0
        assert submitted.incorrect == 0
        assert submitted.omitted == 3
        assert submitted.percentage == 0.0

    def test_get_by_candidate(self, store):
        """Test retrieving assessments for a candidate."""
        # Create multiple assessments for same candidate
        store.create(candidate_id="user123", subject="Anatomy")
        store.create(candidate_id="user123", subject="Physiology")
        store.create(candidate_id="user456", subject="Anatomy")

        assessments = store.get_by_candidate("user123")

        assert len(assessments) == 2
        assert all(a.candidate_id == "user123" for a in assessments)

    def test_get_by_candidate_with_status_filter(self, store):
        """Test retrieving assessments with status filter."""
        # Create and start one assessment
        assessment1 = store.create(candidate_id="user123")
        store.start(assessment1.assessment_id, ["q1", "q2"])

        # Create another but don't start it
        store.create(candidate_id="user123")

        # Get in-progress assessments
        in_progress = store.get_by_candidate("user123", status="in-progress")
        assert len(in_progress) == 1
        assert in_progress[0].status == "in-progress"

        # Get created assessments
        created = store.get_by_candidate("user123", status="created")
        assert len(created) == 1
        assert created[0].status == "created"

    def test_get_by_candidate_with_limit(self, store):
        """Test retrieving assessments with limit."""
        # Create multiple assessments
        for i in range(5):
            store.create(candidate_id="user123")

        assessments = store.get_by_candidate("user123", limit=3)

        assert len(assessments) == 3

    def test_get_score(self, store):
        """Test retrieving score for completed assessment."""
        assessment = store.create(candidate_id="user123")
        store.start(assessment.assessment_id, ["q1", "q2"])
        store.submit(
            assessment.assessment_id, {"q1": "A", "q2": "B"}, {"q1": "A", "q2": "B"}
        )

        score = store.get_score(assessment.assessment_id)

        assert score is not None
        assert score.total_questions == 2
        assert score.correct == 2
        assert score.percentage == 100.0

    def test_get_score_for_incomplete_assessment(self, store):
        """Test retrieving score for incomplete assessment returns None."""
        assessment = store.create(candidate_id="user123")

        score = store.get_score(assessment.assessment_id)

        assert score is None

    def test_delete_assessment(self, store):
        """Test deleting an assessment."""
        assessment = store.create(candidate_id="user123")

        # Delete the assessment
        deleted = store.delete(assessment.assessment_id)
        assert deleted is True

        # Verify it's gone
        retrieved = store.get(assessment.assessment_id)
        assert retrieved is None

    def test_delete_nonexistent_assessment(self, store):
        """Test deleting a non-existent assessment."""
        deleted = store.delete("nonexistent")
        assert deleted is False

    def test_start_assessment_invalid_state(self, store):
        """Test starting an assessment that's already started."""
        assessment = store.create(candidate_id="user123")
        store.start(assessment.assessment_id, ["q1", "q2"])

        # Try to start again
        with pytest.raises(ValueError, match="cannot be started"):
            store.start(assessment.assessment_id, ["q3", "q4"])

    def test_submit_assessment_not_started(self, store):
        """Test submitting an assessment that hasn't been started."""
        assessment = store.create(candidate_id="user123")

        with pytest.raises(ValueError, match="must be started"):
            store.submit(assessment.assessment_id, {}, {})

    def test_question_count_property(self, store):
        """Test question_count property."""
        assert store.question_count == 10
