"""Database operations for user performance analytics."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from sqlmodel import Session, SQLModel, create_engine, select, func
from sqlalchemy import and_

from .user_models import (
    QuestionAttemptDB,
    UserAnalyticsSummaryDB,
    SubjectPerformance,
    SystemPerformance,
    DifficultyPerformance,
    DailyPerformance,
    WeakArea,
    UserAnalytics,
    PercentileRanking,
)


class UserAnalyticsStore:
    """Database store for user performance analytics."""

    def __init__(self, db_path: str = "analytics.db"):
        """Initialize the analytics store with a database connection."""
        if not db_path.startswith("sqlite:///"):
            db_path = f"sqlite:///{db_path}"

        self.engine = create_engine(db_path, echo=False)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        from .user_models import QuestionAttemptDB, UserAnalyticsSummaryDB
        SQLModel.metadata.create_all(self.engine)

    def record_attempt(
        self,
        user_id: Optional[int],
        question_id: str,
        correct_answer: str,
        is_correct: bool,
        assessment_id: Optional[str] = None,
        answer_given: Optional[str] = None,
        subject: Optional[str] = None,
        system: Optional[str] = None,
        difficulty: Optional[str] = None,
        time_seconds: Optional[int] = None,
        mode: str = "practice",
        marked: bool = False,
        omitted: bool = False,
    ) -> QuestionAttemptDB:
        """Record a question attempt."""
        attempt = QuestionAttemptDB(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            subject=subject,
            system=system,
            difficulty=difficulty,
            answer_given=answer_given,
            correct_answer=correct_answer,
            is_correct=is_correct,
            time_seconds=time_seconds,
            mode=mode,
            marked=marked,
            omitted=omitted,
            attempted_at=datetime.utcnow(),
        )

        with Session(self.engine) as session:
            session.add(attempt)
            session.commit()
            session.refresh(attempt)

        # Invalidate cached summary for this user
        self._invalidate_summary_cache(user_id)

        return attempt

    def get_user_attempts(
        self,
        user_id: int,
        limit: Optional[int] = None,
        subject: Optional[str] = None,
        system: Optional[str] = None,
    ) -> list[QuestionAttemptDB]:
        """Retrieve attempts for a user with optional filtering."""
        with Session(self.engine) as session:
            statement = select(QuestionAttemptDB).where(
                QuestionAttemptDB.user_id == user_id
            )

            if subject:
                statement = statement.where(QuestionAttemptDB.subject == subject)
            if system:
                statement = statement.where(QuestionAttemptDB.system == system)

            statement = statement.order_by(QuestionAttemptDB.attempted_at.desc())

            if limit:
                statement = statement.limit(limit)

            return list(session.exec(statement).all())

    def compute_user_analytics(self, user_id: int, days: int = 30) -> UserAnalytics:
        """Compute comprehensive analytics for a user."""
        with Session(self.engine) as session:
            # Get all attempts for the user
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            statement = select(QuestionAttemptDB).where(
                and_(
                    QuestionAttemptDB.user_id == user_id,
                    QuestionAttemptDB.attempted_at >= cutoff_date,
                )
            )
            attempts = list(session.exec(statement).all())

            if not attempts:
                return self._empty_analytics(user_id)

            # Overall metrics
            total_attempts = len(attempts)
            correct_attempts = sum(1 for a in attempts if a.is_correct)
            incorrect_attempts = sum(1 for a in attempts if not a.is_correct and not a.omitted)
            omitted_attempts = sum(1 for a in attempts if a.omitted)
            accuracy_percent = (
                (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0.0
            )

            # Time metrics
            time_attempts = [a for a in attempts if a.time_seconds is not None]
            average_time_seconds = (
                sum(a.time_seconds for a in time_attempts) / len(time_attempts)
                if time_attempts
                else 0.0
            )
            total_study_time_seconds = sum(a.time_seconds or 0 for a in attempts)
            total_study_time_hours = total_study_time_seconds / 3600

            # Unique counts
            questions_attempted_count = len(set(a.question_id for a in attempts))
            assessments_completed = len(set(a.assessment_id for a in attempts if a.assessment_id))

            # Subject breakdown
            by_subject = self._compute_subject_performance(attempts)

            # System breakdown
            by_system = self._compute_system_performance(attempts)

            # Difficulty breakdown
            by_difficulty = self._compute_difficulty_performance(attempts)

            # Daily performance
            daily_performance = self._compute_daily_performance(attempts)

            # Streak calculation
            current_streak_days = self._compute_streak(session, user_id)

            # Weak areas
            weak_areas = self._identify_weak_areas(by_subject, by_system)

            # Strongest/weakest subjects
            strongest_subject = None
            weakest_subject = None
            if by_subject:
                sorted_subjects = sorted(by_subject, key=lambda x: x.accuracy_percent, reverse=True)
                strongest_subject = sorted_subjects[0].subject
                weakest_subject = sorted_subjects[-1].subject

            # Timestamps
            first_attempt_at = min(a.attempted_at for a in attempts)
            last_attempt_at = max(a.attempted_at for a in attempts)

            return UserAnalytics(
                user_id=user_id,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                incorrect_attempts=incorrect_attempts,
                omitted_attempts=omitted_attempts,
                accuracy_percent=round(accuracy_percent, 2),
                average_time_seconds=round(average_time_seconds, 2),
                total_study_time_hours=round(total_study_time_hours, 2),
                questions_attempted_count=questions_attempted_count,
                assessments_completed=assessments_completed,
                current_streak_days=current_streak_days,
                by_subject=by_subject,
                by_system=by_system,
                by_difficulty=by_difficulty,
                daily_performance=daily_performance,
                weak_areas=weak_areas,
                strongest_subject=strongest_subject,
                weakest_subject=weakest_subject,
                first_attempt_at=first_attempt_at,
                last_attempt_at=last_attempt_at,
            )

    def compute_percentile_ranking(self, user_id: int) -> PercentileRanking:
        """Compute user's percentile ranking compared to all users."""
        with Session(self.engine) as session:
            # Get user's stats
            user_statement = select(QuestionAttemptDB).where(
                QuestionAttemptDB.user_id == user_id
            )
            user_attempts = list(session.exec(user_statement).all())

            if not user_attempts:
                return PercentileRanking(
                    user_id=user_id,
                    overall_percentile=0.0,
                    accuracy_percentile=0.0,
                    speed_percentile=0.0,
                    volume_percentile=0.0,
                    total_users=0,
                )

            user_correct = sum(1 for a in user_attempts if a.is_correct)
            user_accuracy = user_correct / len(user_attempts) if user_attempts else 0
            user_time_attempts = [a for a in user_attempts if a.time_seconds is not None]
            user_avg_time = (
                sum(a.time_seconds for a in user_time_attempts) / len(user_time_attempts)
                if user_time_attempts
                else 0
            )
            user_volume = len(user_attempts)

            # Get all users' stats
            all_users_statement = select(QuestionAttemptDB.user_id).distinct()
            all_user_ids = list(session.exec(all_users_statement).all())
            total_users = len(all_user_ids)

            if total_users <= 1:
                return PercentileRanking(
                    user_id=user_id,
                    overall_percentile=100.0,
                    accuracy_percentile=100.0,
                    speed_percentile=100.0,
                    volume_percentile=100.0,
                    total_users=total_users,
                )

            # Calculate percentiles
            better_accuracy = 0
            better_speed = 0
            better_volume = 0

            for other_user_id in all_user_ids:
                if other_user_id == user_id:
                    continue

                other_statement = select(QuestionAttemptDB).where(
                    QuestionAttemptDB.user_id == other_user_id
                )
                other_attempts = list(session.exec(other_statement).all())

                if not other_attempts:
                    continue

                # Accuracy comparison
                other_correct = sum(1 for a in other_attempts if a.is_correct)
                other_accuracy = other_correct / len(other_attempts)
                if user_accuracy > other_accuracy:
                    better_accuracy += 1

                # Speed comparison (lower is better)
                other_time_attempts = [a for a in other_attempts if a.time_seconds is not None]
                if other_time_attempts:
                    other_avg_time = sum(a.time_seconds for a in other_time_attempts) / len(
                        other_time_attempts
                    )
                    if user_avg_time > 0 and user_avg_time < other_avg_time:
                        better_speed += 1

                # Volume comparison
                if user_volume > len(other_attempts):
                    better_volume += 1

            accuracy_percentile = (better_accuracy / (total_users - 1)) * 100
            speed_percentile = (better_speed / (total_users - 1)) * 100 if user_avg_time > 0 else 0
            volume_percentile = (better_volume / (total_users - 1)) * 100

            # Overall percentile (weighted average)
            overall_percentile = (
                accuracy_percentile * 0.5 + speed_percentile * 0.25 + volume_percentile * 0.25
            )

            return PercentileRanking(
                user_id=user_id,
                overall_percentile=round(overall_percentile, 2),
                accuracy_percentile=round(accuracy_percentile, 2),
                speed_percentile=round(speed_percentile, 2),
                volume_percentile=round(volume_percentile, 2),
                total_users=total_users,
            )

    def _compute_subject_performance(
        self, attempts: list[QuestionAttemptDB]
    ) -> list[SubjectPerformance]:
        """Compute performance breakdown by subject."""
        subject_data: dict[str, dict] = {}

        for attempt in attempts:
            if not attempt.subject:
                continue

            if attempt.subject not in subject_data:
                subject_data[attempt.subject] = {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "time_sum": 0,
                    "time_count": 0,
                }

            data = subject_data[attempt.subject]
            data["total"] += 1
            if attempt.is_correct:
                data["correct"] += 1
            elif not attempt.omitted:
                data["incorrect"] += 1

            if attempt.time_seconds is not None:
                data["time_sum"] += attempt.time_seconds
                data["time_count"] += 1

        result = []
        for subject, data in subject_data.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_time = data["time_sum"] / data["time_count"] if data["time_count"] > 0 else 0

            result.append(
                SubjectPerformance(
                    subject=subject,
                    total_attempts=data["total"],
                    correct=data["correct"],
                    incorrect=data["incorrect"],
                    accuracy_percent=round(accuracy, 2),
                    average_time_seconds=round(avg_time, 2),
                )
            )

        return sorted(result, key=lambda x: x.accuracy_percent, reverse=True)

    def _compute_system_performance(
        self, attempts: list[QuestionAttemptDB]
    ) -> list[SystemPerformance]:
        """Compute performance breakdown by organ system."""
        system_data: dict[str, dict] = {}

        for attempt in attempts:
            if not attempt.system:
                continue

            if attempt.system not in system_data:
                system_data[attempt.system] = {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "time_sum": 0,
                    "time_count": 0,
                }

            data = system_data[attempt.system]
            data["total"] += 1
            if attempt.is_correct:
                data["correct"] += 1
            elif not attempt.omitted:
                data["incorrect"] += 1

            if attempt.time_seconds is not None:
                data["time_sum"] += attempt.time_seconds
                data["time_count"] += 1

        result = []
        for system, data in system_data.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_time = data["time_sum"] / data["time_count"] if data["time_count"] > 0 else 0

            result.append(
                SystemPerformance(
                    system=system,
                    total_attempts=data["total"],
                    correct=data["correct"],
                    incorrect=data["incorrect"],
                    accuracy_percent=round(accuracy, 2),
                    average_time_seconds=round(avg_time, 2),
                )
            )

        return sorted(result, key=lambda x: x.accuracy_percent, reverse=True)

    def _compute_difficulty_performance(
        self, attempts: list[QuestionAttemptDB]
    ) -> list[DifficultyPerformance]:
        """Compute performance breakdown by difficulty."""
        difficulty_data: dict[str, dict] = {}

        for attempt in attempts:
            if not attempt.difficulty:
                continue

            if attempt.difficulty not in difficulty_data:
                difficulty_data[attempt.difficulty] = {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                }

            data = difficulty_data[attempt.difficulty]
            data["total"] += 1
            if attempt.is_correct:
                data["correct"] += 1
            elif not attempt.omitted:
                data["incorrect"] += 1

        result = []
        for difficulty, data in difficulty_data.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0

            result.append(
                DifficultyPerformance(
                    difficulty=difficulty,
                    total_attempts=data["total"],
                    correct=data["correct"],
                    incorrect=data["incorrect"],
                    accuracy_percent=round(accuracy, 2),
                )
            )

        # Sort by difficulty order
        difficulty_order = {"Easy": 0, "Medium": 1, "Hard": 2}
        return sorted(result, key=lambda x: difficulty_order.get(x.difficulty, 99))

    def _compute_daily_performance(
        self, attempts: list[QuestionAttemptDB]
    ) -> list[DailyPerformance]:
        """Compute daily performance time series."""
        daily_data: dict[str, dict] = {}

        for attempt in attempts:
            date_str = attempt.attempted_at.date().isoformat()

            if date_str not in daily_data:
                daily_data[date_str] = {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "time_sum": 0,
                }

            data = daily_data[date_str]
            data["total"] += 1
            if attempt.is_correct:
                data["correct"] += 1
            elif not attempt.omitted:
                data["incorrect"] += 1

            if attempt.time_seconds is not None:
                data["time_sum"] += attempt.time_seconds

        result = []
        for date_str, data in daily_data.items():
            accuracy = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0

            result.append(
                DailyPerformance(
                    date=date_str,
                    total_attempts=data["total"],
                    correct=data["correct"],
                    incorrect=data["incorrect"],
                    accuracy_percent=round(accuracy, 2),
                    study_time_seconds=data["time_sum"],
                )
            )

        return sorted(result, key=lambda x: x.date)

    def _compute_streak(self, session: Session, user_id: int) -> int:
        """Compute current consecutive days streak."""
        # Get unique dates of attempts
        statement = (
            select(QuestionAttemptDB.attempted_at)
            .where(QuestionAttemptDB.user_id == user_id)
            .order_by(QuestionAttemptDB.attempted_at.desc())
        )

        attempts = list(session.exec(statement).all())
        if not attempts:
            return 0

        # Extract unique dates
        unique_dates = sorted(set(a.date() for a in attempts), reverse=True)

        streak = 0
        today = datetime.utcnow().date()

        # Check if user has attempted today or yesterday
        if unique_dates[0] < today - timedelta(days=1):
            return 0

        for i, date in enumerate(unique_dates):
            expected_date = today - timedelta(days=i)
            if date == expected_date or date == expected_date - timedelta(days=1):
                streak += 1
            else:
                break

        return streak

    def _identify_weak_areas(
        self,
        by_subject: list[SubjectPerformance],
        by_system: list[SystemPerformance],
    ) -> list[WeakArea]:
        """Identify weak performance areas."""
        weak_areas = []

        # Find subjects with accuracy below 70% and at least 10 attempts
        weak_subjects = [
            s for s in by_subject if s.accuracy_percent < 70 and s.total_attempts >= 10
        ]
        for i, subject in enumerate(sorted(weak_subjects, key=lambda x: x.accuracy_percent)):
            weak_areas.append(
                WeakArea(
                    category="subject",
                    name=subject.subject,
                    total_attempts=subject.total_attempts,
                    accuracy_percent=subject.accuracy_percent,
                    rank=i + 1,
                )
            )

        # Find systems with accuracy below 70% and at least 10 attempts
        weak_systems = [
            s for s in by_system if s.accuracy_percent < 70 and s.total_attempts >= 10
        ]
        for i, system in enumerate(sorted(weak_systems, key=lambda x: x.accuracy_percent)):
            weak_areas.append(
                WeakArea(
                    category="system",
                    name=system.system,
                    total_attempts=system.total_attempts,
                    accuracy_percent=system.accuracy_percent,
                    rank=i + 1,
                )
            )

        return weak_areas

    def _invalidate_summary_cache(self, user_id: Optional[int]) -> None:
        """Remove cached summary for a user."""
        if user_id is None:
            return

        with Session(self.engine) as session:
            statement = select(UserAnalyticsSummaryDB).where(
                UserAnalyticsSummaryDB.user_id == user_id
            )
            summary = session.exec(statement).first()
            if summary:
                session.delete(summary)
                session.commit()

    def _empty_analytics(self, user_id: int) -> UserAnalytics:
        """Return empty analytics for users with no attempts."""
        return UserAnalytics(
            user_id=user_id,
            total_attempts=0,
            correct_attempts=0,
            incorrect_attempts=0,
            omitted_attempts=0,
            accuracy_percent=0.0,
            average_time_seconds=0.0,
            total_study_time_hours=0.0,
            questions_attempted_count=0,
            assessments_completed=0,
            current_streak_days=0,
            by_subject=[],
            by_system=[],
            by_difficulty=[],
            daily_performance=[],
            weak_areas=[],
            strongest_subject=None,
            weakest_subject=None,
            first_attempt_at=None,
            last_attempt_at=None,
        )


__all__ = ["UserAnalyticsStore"]
