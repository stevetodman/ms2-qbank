"""SM-2 Spaced Repetition Algorithm implementation.

This module implements the SuperMemo 2 (SM-2) algorithm for optimal card review scheduling.
The algorithm adjusts review intervals based on how well the user recalls the card.

References:
- https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
- https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2_algorithm
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass
class ReviewState:
    """Current spaced repetition state for a flashcard."""

    ease_factor: float  # Quality of recall (default 2.5, min 1.3)
    interval_days: int  # Days until next review
    repetitions: int  # Number of consecutive correct reviews
    next_review_date: date
    streak: int  # Current streak of correct answers (quality >= 3)


class SpacedRepetitionScheduler:
    """
    SM-2 algorithm scheduler for flashcard reviews.

    Quality ratings (0-5 scale):
        0: Complete blackout - no recall at all
        1: Incorrect response, but familiar with the answer
        2: Incorrect response, but easy to recall correct answer upon seeing it
        3: Correct response, but with difficulty
        4: Correct response with some hesitation
        5: Perfect recall, immediate correct response

    The algorithm works as follows:
    - Quality < 3: Reset repetitions to 0, short interval (restart learning)
    - Quality >= 3: Increase interval exponentially based on ease factor
    - Ease factor adjusts based on quality (harder cards decrease ease factor)
    """

    # Minimum ease factor (prevents cards from being scheduled too frequently)
    MIN_EASE_FACTOR = 1.3

    # Initial ease factor for new cards
    INITIAL_EASE_FACTOR = 2.5

    # Hard-coded intervals for first repetitions (in days)
    FIRST_INTERVAL = 1  # Review again in 1 day
    SECOND_INTERVAL = 6  # Review again in 6 days

    def __init__(self) -> None:
        """Initialize the spaced repetition scheduler."""
        pass

    def calculate_next_review(
        self,
        current_state: ReviewState,
        quality: int,
    ) -> ReviewState:
        """
        Calculate next review date based on current state and quality rating.

        Args:
            current_state: Current review state for the card
            quality: Quality rating from 0-5

        Returns:
            New review state with updated intervals and ease factor

        Raises:
            ValueError: If quality is not in range 0-5
        """
        if not 0 <= quality <= 5:
            raise ValueError(f"Quality must be between 0 and 5, got {quality}")

        # Clone current state
        ease_factor = current_state.ease_factor
        interval_days = current_state.interval_days
        repetitions = current_state.repetitions
        streak = current_state.streak

        # If quality < 3, the answer was incorrect - restart learning
        if quality < 3:
            repetitions = 0
            interval_days = self.FIRST_INTERVAL
            streak = 0  # Reset streak on failure
        else:
            # Correct answer - update streak
            streak += 1

            # Calculate new interval based on repetition number
            if repetitions == 0:
                interval_days = self.FIRST_INTERVAL
            elif repetitions == 1:
                interval_days = self.SECOND_INTERVAL
            else:
                # Use ease factor for subsequent intervals
                interval_days = round(interval_days * ease_factor)

            # Increment repetition counter
            repetitions += 1

        # Update ease factor based on quality
        # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        # Ensure ease factor doesn't go below minimum
        ease_factor = max(self.MIN_EASE_FACTOR, ease_factor)

        # Calculate next review date
        next_review_date = date.today() + timedelta(days=interval_days)

        return ReviewState(
            ease_factor=round(ease_factor, 2),
            interval_days=interval_days,
            repetitions=repetitions,
            next_review_date=next_review_date,
            streak=streak,
        )

    def create_initial_state(self) -> ReviewState:
        """
        Create initial review state for a new card.

        Returns:
            Initial review state with default values
        """
        return ReviewState(
            ease_factor=self.INITIAL_EASE_FACTOR,
            interval_days=0,
            repetitions=0,
            next_review_date=date.today(),  # Due immediately
            streak=0,
        )

    def is_due(self, next_review_date: date) -> bool:
        """
        Check if a card is due for review.

        Args:
            next_review_date: Scheduled next review date

        Returns:
            True if card should be reviewed today or earlier
        """
        return next_review_date <= date.today()

    def days_until_review(self, next_review_date: date) -> int:
        """
        Calculate days until next review.

        Args:
            next_review_date: Scheduled next review date

        Returns:
            Number of days (negative if overdue)
        """
        delta = next_review_date - date.today()
        return delta.days


__all__ = ["ReviewState", "SpacedRepetitionScheduler"]
