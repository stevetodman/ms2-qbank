"""FastAPI application for flashcard system with spaced repetition."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status

from .models import (
    CardCreate,
    CardResponse,
    CardUpdate,
    DeckCreate,
    DeckResponse,
    DeckStatsResponse,
    DeckUpdate,
    ReviewResponse,
    ReviewSubmit,
)
from .store import FlashcardStore


def create_app(*, store: Optional[FlashcardStore] = None) -> FastAPI:
    """Create and configure the flashcard FastAPI application.

    Args:
        store: Optional FlashcardStore instance for dependency injection (testing)

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(title="MS2 QBank Flashcard API", version="1.0.0")

    # Initialize flashcard store
    flashcard_store = store or FlashcardStore()
    app.state.flashcard_store = flashcard_store

    def get_store() -> FlashcardStore:
        """Dependency to get the flashcard store instance."""
        return app.state.flashcard_store

    # ===== DECK ENDPOINTS =====

    @app.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
    def create_deck(
        payload: DeckCreate,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> DeckResponse:
        """Create a new flashcard deck."""
        deck = store.create_deck(
            name=payload.name,
            description=payload.description,
            deck_type=payload.deck_type,
            category=payload.category,
            user_id=user_id,
        )

        # Get card count and due count
        stats = store.get_deck_stats(deck.id, user_id)

        return DeckResponse(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            deck_type=deck.deck_type,
            category=deck.category,
            is_active=deck.is_active,
            is_public=deck.is_public,
            card_count=stats["total_cards"],
            due_count=stats["cards_due_today"],
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )

    @app.get("/decks", response_model=list[DeckResponse])
    def list_decks(
        deck_type: Optional[str] = None,
        active_only: bool = True,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> list[DeckResponse]:
        """List all flashcard decks."""
        decks = store.list_decks(
            user_id=user_id,
            deck_type=deck_type,
            active_only=active_only,
        )

        responses: list[DeckResponse] = []
        for deck in decks:
            stats = store.get_deck_stats(deck.id, user_id)
            responses.append(
                DeckResponse(
                    id=deck.id,
                    name=deck.name,
                    description=deck.description,
                    deck_type=deck.deck_type,
                    category=deck.category,
                    is_active=deck.is_active,
                    is_public=deck.is_public,
                    card_count=stats["total_cards"],
                    due_count=stats["cards_due_today"],
                    created_at=deck.created_at,
                    updated_at=deck.updated_at,
                )
            )

        return responses

    @app.get("/decks/{deck_id}", response_model=DeckResponse)
    def get_deck(
        deck_id: int,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> DeckResponse:
        """Get a specific deck by ID."""
        deck = store.get_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

        stats = store.get_deck_stats(deck.id, user_id)

        return DeckResponse(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            deck_type=deck.deck_type,
            category=deck.category,
            is_active=deck.is_active,
            is_public=deck.is_public,
            card_count=stats["total_cards"],
            due_count=stats["cards_due_today"],
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )

    @app.patch("/decks/{deck_id}", response_model=DeckResponse)
    def update_deck(
        deck_id: int,
        payload: DeckUpdate,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> DeckResponse:
        """Update deck metadata."""
        deck = store.update_deck(
            deck_id=deck_id,
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
        )

        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

        stats = store.get_deck_stats(deck.id, user_id)

        return DeckResponse(
            id=deck.id,
            name=deck.name,
            description=deck.description,
            deck_type=deck.deck_type,
            category=deck.category,
            is_active=deck.is_active,
            is_public=deck.is_public,
            card_count=stats["total_cards"],
            due_count=stats["cards_due_today"],
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )

    @app.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_deck(
        deck_id: int,
        store: FlashcardStore = Depends(get_store),
    ) -> None:
        """Delete a deck and all its cards."""
        deleted = store.delete_deck(deck_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

    @app.get("/decks/{deck_id}/stats", response_model=DeckStatsResponse)
    def get_deck_stats(
        deck_id: int,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> DeckStatsResponse:
        """Get detailed statistics for a deck."""
        deck = store.get_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

        stats = store.get_deck_stats(deck_id, user_id)

        return DeckStatsResponse(
            deck_id=deck_id,
            total_cards=stats["total_cards"],
            new_cards=stats["new_cards"],
            learning_cards=stats["learning_cards"],
            mature_cards=stats["mature_cards"],
            cards_due_today=stats["cards_due_today"],
            average_ease_factor=stats["average_ease_factor"],
            total_reviews=stats["total_reviews"],
            accuracy_percentage=stats["accuracy_percentage"],
        )

    # ===== CARD ENDPOINTS =====

    @app.post("/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
    def create_card(
        payload: CardCreate,
        store: FlashcardStore = Depends(get_store),
    ) -> CardResponse:
        """Create a new flashcard."""
        # Verify deck exists
        deck = store.get_deck(payload.deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {payload.deck_id} not found",
            )

        card = store.create_card(
            deck_id=payload.deck_id,
            front=payload.front,
            back=payload.back,
            hint=payload.hint,
            tags=payload.tags,
            source_question_id=payload.source_question_id,
        )

        return CardResponse(
            id=card.id,
            deck_id=card.deck_id,
            front=card.front,
            back=card.back,
            hint=card.hint,
            tags=json.loads(card.tags),
            source_question_id=card.source_question_id,
            difficulty=card.difficulty,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )

    @app.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
    def list_cards(
        deck_id: int,
        store: FlashcardStore = Depends(get_store),
    ) -> list[CardResponse]:
        """List all cards in a deck."""
        # Verify deck exists
        deck = store.get_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

        cards = store.list_cards(deck_id)

        return [
            CardResponse(
                id=card.id,
                deck_id=card.deck_id,
                front=card.front,
                back=card.back,
                hint=card.hint,
                tags=json.loads(card.tags),
                source_question_id=card.source_question_id,
                difficulty=card.difficulty,
                created_at=card.created_at,
                updated_at=card.updated_at,
            )
            for card in cards
        ]

    @app.get("/cards/{card_id}", response_model=CardResponse)
    def get_card(
        card_id: int,
        store: FlashcardStore = Depends(get_store),
    ) -> CardResponse:
        """Get a specific card by ID."""
        card = store.get_card(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card {card_id} not found",
            )

        return CardResponse(
            id=card.id,
            deck_id=card.deck_id,
            front=card.front,
            back=card.back,
            hint=card.hint,
            tags=json.loads(card.tags),
            source_question_id=card.source_question_id,
            difficulty=card.difficulty,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )

    @app.patch("/cards/{card_id}", response_model=CardResponse)
    def update_card(
        card_id: int,
        payload: CardUpdate,
        store: FlashcardStore = Depends(get_store),
    ) -> CardResponse:
        """Update card content."""
        card = store.update_card(
            card_id=card_id,
            front=payload.front,
            back=payload.back,
            hint=payload.hint,
            tags=payload.tags,
        )

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card {card_id} not found",
            )

        return CardResponse(
            id=card.id,
            deck_id=card.deck_id,
            front=card.front,
            back=card.back,
            hint=card.hint,
            tags=json.loads(card.tags),
            source_question_id=card.source_question_id,
            difficulty=card.difficulty,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )

    @app.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_card(
        card_id: int,
        store: FlashcardStore = Depends(get_store),
    ) -> None:
        """Delete a card."""
        deleted = store.delete_card(card_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card {card_id} not found",
            )

    # ===== REVIEW ENDPOINTS =====

    @app.get("/decks/{deck_id}/due", response_model=list[CardResponse])
    def get_due_cards(
        deck_id: int,
        limit: Optional[int] = None,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> list[CardResponse]:
        """Get cards due for review in a deck."""
        # Verify deck exists
        deck = store.get_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deck {deck_id} not found",
            )

        due_cards = store.get_due_cards(deck_id, user_id, limit)

        return [
            CardResponse(
                id=card.id,
                deck_id=card.deck_id,
                front=card.front,
                back=card.back,
                hint=card.hint,
                tags=json.loads(card.tags),
                source_question_id=card.source_question_id,
                difficulty=card.difficulty,
                created_at=card.created_at,
                updated_at=card.updated_at,
            )
            for card, _ in due_cards
        ]

    @app.post("/reviews", response_model=ReviewResponse)
    def submit_review(
        payload: ReviewSubmit,
        store: FlashcardStore = Depends(get_store),
        user_id: Optional[int] = None,  # TODO: Get from auth token
    ) -> ReviewResponse:
        """Submit a card review and update spaced repetition schedule."""
        # Verify card exists
        card = store.get_card(payload.card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card {payload.card_id} not found",
            )

        try:
            review = store.submit_review(
                card_id=payload.card_id,
                quality=payload.quality,
                user_id=user_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return ReviewResponse(
            card_id=review.card_id,
            next_review_date=review.next_review_date,
            interval_days=review.interval_days,
            ease_factor=review.ease_factor,
            streak=review.streak,
        )

    return app


# Create default app instance
app = create_app()

__all__ = ["app", "create_app"]
