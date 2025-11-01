"""Domain models and schemas for the flashcards service."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, JSON, MetaData
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


flashcard_metadata = MetaData()


class DeckType(str, Enum):
    """Classification for the type of deck exposed to learners."""

    READY = "ready"
    SMART = "smart"


class FlashcardBase(SQLModel):
    """Base class configuring shared SQLModel metadata for the service."""

    model_config = ConfigDict(from_attributes=True)
    metadata = flashcard_metadata


class FlashcardDeck(FlashcardBase, table=True):
    """Persistent representation of a flashcard deck."""

    __tablename__ = "flashcard_decks"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    deck_type: DeckType = Field(index=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class FlashcardCard(FlashcardBase, table=True):
    """Persistent representation of an individual flashcard."""

    __tablename__ = "flashcard_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="flashcard_decks.id", index=True, nullable=False)
    prompt: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=4000)
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )
    explanation: Optional[str] = Field(default=None, max_length=4000)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

class DeckBase(SQLModel):
    """Common deck fields shared across request/response payloads."""

    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    deck_type: DeckType


class DeckCreate(DeckBase):
    """Payload for creating a new deck."""


class DeckUpdate(SQLModel):
    """Payload for partially updating a deck."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    deck_type: Optional[DeckType] = None


class DeckSummary(DeckBase):
    """Deck representation returned in list responses."""

    id: int
    created_at: datetime
    updated_at: datetime
    card_count: int


class DeckDetail(DeckSummary):
    """Detailed deck representation including cards."""

    cards: list["CardRead"]


class CardBase(SQLModel):
    """Common flashcard fields used across payloads."""

    prompt: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=4000)
    tags: list[str] = Field(default_factory=list)
    explanation: Optional[str] = Field(default=None, max_length=4000)


class CardCreate(CardBase):
    """Payload for creating a new card."""


class CardUpdate(SQLModel):
    """Payload for updating an existing card."""

    prompt: Optional[str] = Field(default=None, min_length=1, max_length=500)
    answer: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    tags: Optional[list[str]] = None
    explanation: Optional[str] = Field(default=None, max_length=4000)


class CardRead(CardBase):
    """Card representation returned to clients."""

    id: int
    deck_id: int
    created_at: datetime
    updated_at: datetime

