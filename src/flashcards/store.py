"""Database-backed persistence for flashcards and reviews."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select, func

from .models import CardReviewDB, DeckDB, FlashcardDB
from .spaced_repetition import ReviewState, SpacedRepetitionScheduler


class FlashcardStore:
    """Handle flashcard data persistence with SQLite database."""

    def __init__(self, database_url: str = "sqlite:///data/flashcards.db") -> None:
        """Initialize the flashcard store with a database connection.

        Args:
            database_url: SQLAlchemy database URL
        """
        # Ensure data directory exists
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(database_url, echo=False)
        SQLModel.metadata.create_all(self.engine)
        self.scheduler = SpacedRepetitionScheduler()

    # Deck operations ----------------------------------------------------------

    def create_deck(
        self,
        name: str,
        deck_type: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> DeckDB:
        """Create a new flashcard deck."""
        with Session(self.engine) as session:
            deck = DeckDB(
                name=name,
                description=description,
                deck_type=deck_type,
                category=category,
                user_id=user_id,
            )
            session.add(deck)
            session.commit()
            session.refresh(deck)
            return deck

    def get_deck(self, deck_id: int) -> Optional[DeckDB]:
        """Retrieve a deck by ID."""
        with Session(self.engine) as session:
            return session.get(DeckDB, deck_id)

    def list_decks(
        self,
        user_id: Optional[int] = None,
        deck_type: Optional[str] = None,
        active_only: bool = True,
    ) -> list[DeckDB]:
        """List decks with optional filtering."""
        with Session(self.engine) as session:
            query = select(DeckDB)

            if user_id is not None:
                query = query.where(DeckDB.user_id == user_id)
            if deck_type:
                query = query.where(DeckDB.deck_type == deck_type)
            if active_only:
                query = query.where(DeckDB.is_active == True)

            query = query.order_by(DeckDB.created_at.desc())
            return list(session.exec(query).all())

    def update_deck(
        self,
        deck_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[DeckDB]:
        """Update deck metadata."""
        with Session(self.engine) as session:
            deck = session.get(DeckDB, deck_id)
            if not deck:
                return None

            if name is not None:
                deck.name = name
            if description is not None:
                deck.description = description
            if is_active is not None:
                deck.is_active = is_active

            deck.updated_at = datetime.now(timezone.utc)

            session.add(deck)
            session.commit()
            session.refresh(deck)
            return deck

    def delete_deck(self, deck_id: int) -> bool:
        """Delete a deck and all its cards."""
        with Session(self.engine) as session:
            deck = session.get(DeckDB, deck_id)
            if not deck:
                return False

            # Delete all cards in the deck
            cards = session.exec(select(FlashcardDB).where(FlashcardDB.deck_id == deck_id)).all()
            for card in cards:
                # Delete card reviews
                reviews = session.exec(
                    select(CardReviewDB).where(CardReviewDB.card_id == card.id)
                ).all()
                for review in reviews:
                    session.delete(review)
                # Delete card
                session.delete(card)

            # Delete deck
            session.delete(deck)
            session.commit()
            return True

    # Card operations ----------------------------------------------------------

    def create_card(
        self,
        deck_id: int,
        front: str,
        back: str,
        hint: Optional[str] = None,
        tags: Optional[list[str]] = None,
        source_question_id: Optional[str] = None,
    ) -> FlashcardDB:
        """Create a new flashcard."""
        with Session(self.engine) as session:
            card = FlashcardDB(
                deck_id=deck_id,
                front=front,
                back=back,
                hint=hint,
                tags=json.dumps(tags or []),
                source_question_id=source_question_id,
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            return card

    def get_card(self, card_id: int) -> Optional[FlashcardDB]:
        """Retrieve a card by ID."""
        with Session(self.engine) as session:
            return session.get(FlashcardDB, card_id)

    def list_cards(self, deck_id: int) -> list[FlashcardDB]:
        """List all cards in a deck."""
        with Session(self.engine) as session:
            query = select(FlashcardDB).where(FlashcardDB.deck_id == deck_id)
            query = query.order_by(FlashcardDB.created_at)
            return list(session.exec(query).all())

    def update_card(
        self,
        card_id: int,
        front: Optional[str] = None,
        back: Optional[str] = None,
        hint: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Optional[FlashcardDB]:
        """Update card content."""
        with Session(self.engine) as session:
            card = session.get(FlashcardDB, card_id)
            if not card:
                return None

            if front is not None:
                card.front = front
            if back is not None:
                card.back = back
            if hint is not None:
                card.hint = hint
            if tags is not None:
                card.tags = json.dumps(tags)

            card.updated_at = datetime.now(timezone.utc)

            session.add(card)
            session.commit()
            session.refresh(card)
            return card

    def delete_card(self, card_id: int) -> bool:
        """Delete a card and its review history."""
        with Session(self.engine) as session:
            card = session.get(FlashcardDB, card_id)
            if not card:
                return False

            # Delete reviews
            reviews = session.exec(select(CardReviewDB).where(CardReviewDB.card_id == card_id)).all()
            for review in reviews:
                session.delete(review)

            # Delete card
            session.delete(card)
            session.commit()
            return True

    # Review operations --------------------------------------------------------

    def get_or_create_review_state(
        self,
        card_id: int,
        user_id: Optional[int] = None,
    ) -> CardReviewDB:
        """Get existing review state or create a new one for a card."""
        with Session(self.engine) as session:
            query = select(CardReviewDB).where(CardReviewDB.card_id == card_id)
            if user_id is not None:
                query = query.where(CardReviewDB.user_id == user_id)

            review = session.exec(query).first()

            if review:
                return review

            # Create new review state
            initial_state = self.scheduler.create_initial_state()
            review = CardReviewDB(
                card_id=card_id,
                user_id=user_id,
                ease_factor=initial_state.ease_factor,
                interval_days=initial_state.interval_days,
                repetitions=initial_state.repetitions,
                next_review_date=initial_state.next_review_date,
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review

    def submit_review(
        self,
        card_id: int,
        quality: int,
        user_id: Optional[int] = None,
    ) -> CardReviewDB:
        """Submit a card review and update spaced repetition state."""
        with Session(self.engine) as session:
            # Get or create review state
            query = select(CardReviewDB).where(CardReviewDB.card_id == card_id)
            if user_id is not None:
                query = query.where(CardReviewDB.user_id == user_id)

            review = session.exec(query).first()

            if not review:
                # Create initial state
                initial_state = self.scheduler.create_initial_state()
                review = CardReviewDB(
                    card_id=card_id,
                    user_id=user_id,
                    ease_factor=initial_state.ease_factor,
                    interval_days=initial_state.interval_days,
                    repetitions=initial_state.repetitions,
                    next_review_date=initial_state.next_review_date,
                )

            # Calculate next review using SM-2
            current_state = ReviewState(
                ease_factor=review.ease_factor,
                interval_days=review.interval_days,
                repetitions=review.repetitions,
                next_review_date=review.next_review_date,
                streak=review.streak,
            )

            new_state = self.scheduler.calculate_next_review(current_state, quality)

            # Update review record
            review.ease_factor = new_state.ease_factor
            review.interval_days = new_state.interval_days
            review.repetitions = new_state.repetitions
            review.next_review_date = new_state.next_review_date
            review.streak = new_state.streak
            review.last_quality = quality
            review.last_reviewed_at = datetime.now(timezone.utc)
            review.total_reviews += 1

            if quality >= 3:  # Correct answer
                review.correct_count += 1

            review.updated_at = datetime.now(timezone.utc)

            session.add(review)
            session.commit()
            session.refresh(review)
            return review

    def get_due_cards(
        self,
        deck_id: int,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[tuple[FlashcardDB, CardReviewDB]]:
        """Get cards due for review in a deck."""
        with Session(self.engine) as session:
            # Get all cards in deck
            cards = session.exec(
                select(FlashcardDB).where(FlashcardDB.deck_id == deck_id)
            ).all()

            due_cards: list[tuple[FlashcardDB, CardReviewDB]] = []

            for card in cards:
                review = self.get_or_create_review_state(card.id, user_id)

                if self.scheduler.is_due(review.next_review_date):
                    due_cards.append((card, review))

            # Sort by next review date (most overdue first)
            due_cards.sort(key=lambda x: x[1].next_review_date)

            if limit:
                due_cards = due_cards[:limit]

            return due_cards

    # Statistics ---------------------------------------------------------------

    def get_deck_stats(
        self,
        deck_id: int,
        user_id: Optional[int] = None,
    ) -> dict:
        """Get statistics for a deck."""
        with Session(self.engine) as session:
            # Total cards
            total_cards = session.exec(
                select(func.count(FlashcardDB.id)).where(FlashcardDB.deck_id == deck_id)
            ).one()

            # Get all review states for this deck
            cards = session.exec(
                select(FlashcardDB).where(FlashcardDB.deck_id == deck_id)
            ).all()

            new_cards = 0
            learning_cards = 0
            mature_cards = 0
            cards_due_today = 0
            total_reviews = 0
            correct_reviews = 0
            ease_factors: list[float] = []

            for card in cards:
                review = self.get_or_create_review_state(card.id, user_id)

                # Categorize card
                if review.repetitions == 0:
                    new_cards += 1
                elif review.interval_days < 21:
                    learning_cards += 1
                else:
                    mature_cards += 1

                # Check if due
                if self.scheduler.is_due(review.next_review_date):
                    cards_due_today += 1

                # Aggregate stats
                total_reviews += review.total_reviews
                correct_reviews += review.correct_count
                ease_factors.append(review.ease_factor)

            average_ease = sum(ease_factors) / len(ease_factors) if ease_factors else 2.5
            accuracy = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0.0

            return {
                "total_cards": total_cards,
                "new_cards": new_cards,
                "learning_cards": learning_cards,
                "mature_cards": mature_cards,
                "cards_due_today": cards_due_today,
                "total_reviews": total_reviews,
                "accuracy_percentage": round(accuracy, 2),
                "average_ease_factor": round(average_ease, 2),
            }


__all__ = ["FlashcardStore"]
