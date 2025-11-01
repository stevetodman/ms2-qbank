"""Database models and Pydantic schemas for flashcard system."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import Column, DateTime, Field as SQLField, SQLModel, Text


class DeckDB(SQLModel, table=True):
    """Database model for flashcard decks."""

    __tablename__ = "decks"

    # Primary key
    id: Optional[int] = SQLField(default=None, primary_key=True)

    # User association
    user_id: Optional[int] = SQLField(default=None, index=True)

    # Deck metadata
    name: str = SQLField(max_length=255)
    description: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    deck_type: str = SQLField(max_length=50)  # 'ready' or 'smart'
    category: Optional[str] = SQLField(default=None, max_length=100)  # Anatomy, Pharmacology, etc.

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    # Deck settings
    is_active: bool = SQLField(default=True)
    is_public: bool = SQLField(default=False)  # For future deck sharing


class FlashcardDB(SQLModel, table=True):
    """Database model for individual flashcards."""

    __tablename__ = "flashcards"

    # Primary key
    id: Optional[int] = SQLField(default=None, primary_key=True)

    # Foreign key to deck
    deck_id: int = SQLField(foreign_key="decks.id", index=True)

    # Card content
    front: str = SQLField(sa_column=Column(Text))
    back: str = SQLField(sa_column=Column(Text))
    hint: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Optional source tracking (for cards created from QBank)
    source_question_id: Optional[str] = SQLField(default=None, max_length=100, index=True)

    # Card metadata
    tags: str = SQLField(default="[]")  # JSON array of tags
    difficulty: Optional[str] = SQLField(default=None, max_length=50)

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CardReviewDB(SQLModel, table=True):
    """Database model for tracking card review history and spaced repetition state."""

    __tablename__ = "card_reviews"

    # Primary key
    id: Optional[int] = SQLField(default=None, primary_key=True)

    # Foreign keys
    card_id: int = SQLField(foreign_key="flashcards.id", index=True)
    user_id: Optional[int] = SQLField(default=None, index=True)

    # Spaced repetition state (SM-2 algorithm)
    ease_factor: float = SQLField(default=2.5)  # Quality of recall (starts at 2.5)
    interval_days: int = SQLField(default=0)  # Days until next review
    repetitions: int = SQLField(default=0)  # Number of consecutive correct reviews

    # Review scheduling
    last_reviewed_at: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    next_review_date: date = SQLField(default_factory=date.today)

    # Review quality (0-5 scale from SM-2)
    # 0: Complete blackout
    # 1: Incorrect, but familiar
    # 2: Incorrect, but easy to recall correct answer
    # 3: Correct with difficulty
    # 4: Correct with hesitation
    # 5: Perfect recall
    last_quality: Optional[int] = SQLField(default=None)

    # Statistics
    total_reviews: int = SQLField(default=0)
    correct_count: int = SQLField(default=0)
    streak: int = SQLField(default=0)  # Current streak of correct answers

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone.utc), nullable=False),
    )
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# Pydantic models for API requests/responses


class DeckCreate(BaseModel):
    """Request payload for creating a new deck."""

    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    deck_type: str = Field(pattern="^(ready|smart)$")  # ready or smart
    category: Optional[str] = None


class DeckUpdate(BaseModel):
    """Request payload for updating a deck."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DeckResponse(BaseModel):
    """Response model for deck data."""

    id: int
    name: str
    description: Optional[str]
    deck_type: str
    category: Optional[str]
    is_active: bool
    is_public: bool
    card_count: int = 0  # Will be populated by service
    due_count: int = 0  # Cards due for review today
    created_at: datetime
    updated_at: datetime


class CardCreate(BaseModel):
    """Request payload for creating a flashcard."""

    deck_id: int
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    hint: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source_question_id: Optional[str] = None


class CardUpdate(BaseModel):
    """Request payload for updating a flashcard."""

    front: Optional[str] = Field(default=None, min_length=1)
    back: Optional[str] = Field(default=None, min_length=1)
    hint: Optional[str] = None
    tags: Optional[list[str]] = None


class CardResponse(BaseModel):
    """Response model for flashcard data."""

    id: int
    deck_id: int
    front: str
    back: str
    hint: Optional[str]
    tags: list[str]
    source_question_id: Optional[str]
    difficulty: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReviewSubmit(BaseModel):
    """Request payload for submitting a card review."""

    card_id: int
    quality: int = Field(ge=0, le=5, description="Quality rating 0-5 (SM-2 algorithm)")


class ReviewResponse(BaseModel):
    """Response model for review submission."""

    card_id: int
    next_review_date: date
    interval_days: int
    ease_factor: float
    streak: int


class DeckStatsResponse(BaseModel):
    """Response model for deck statistics."""

    deck_id: int
    total_cards: int
    new_cards: int  # Never reviewed
    learning_cards: int  # Interval < 21 days
    mature_cards: int  # Interval >= 21 days
    cards_due_today: int
    average_ease_factor: float
    total_reviews: int
    accuracy_percentage: float


__all__ = [
    "DeckDB",
    "FlashcardDB",
    "CardReviewDB",
    "DeckCreate",
    "DeckUpdate",
    "DeckResponse",
    "CardCreate",
    "CardUpdate",
    "CardResponse",
    "ReviewSubmit",
    "ReviewResponse",
    "DeckStatsResponse",
]
