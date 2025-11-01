"""FastAPI application exposing flashcard deck and card CRUD endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Iterable, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import Engine, func
from sqlmodel import Session, delete, select, create_engine
from sqlalchemy.pool import StaticPool

from .models import (
    CardCreate,
    CardRead,
    CardUpdate,
    DeckCreate,
    DeckDetail,
    DeckSummary,
    DeckType,
    DeckUpdate,
    FlashcardCard,
    FlashcardDeck,
    flashcard_metadata,
)

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "flashcards" / "flashcards.db"
DEFAULT_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "flashcards" / "seed.json"


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_database_url(database: Optional[str | Path]) -> str:
    if database is None:
        _ensure_directory(DEFAULT_DATABASE_PATH)
        return f"sqlite:///{DEFAULT_DATABASE_PATH}"

    if isinstance(database, Path):
        _ensure_directory(database)
        return f"sqlite:///{database}"

    if database.startswith("sqlite://"):
        if database.startswith("sqlite:///") and not database.startswith("sqlite:////"):
            candidate = Path(database.replace("sqlite:///", "", 1))
            if not candidate.is_absolute():
                candidate = DEFAULT_DATABASE_PATH.parent / candidate
            _ensure_directory(candidate)
        return database

    resolved = Path(database)
    _ensure_directory(resolved)
    return f"sqlite:///{resolved}"


def _create_engine(database_url: str, *, use_static_pool: bool = False) -> Engine:
    if use_static_pool:
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


def _seed_database(session: Session, seed_path: Path) -> None:
    if not seed_path.exists():
        return

    existing = session.exec(select(func.count(FlashcardDeck.id))).one()
    if existing:
        return

    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to load flashcard seed data from {seed_path}") from exc

    for entry in payload:
        deck = FlashcardDeck(
            name=entry["name"],
            description=entry.get("description"),
            deck_type=DeckType(entry.get("deck_type", DeckType.READY)),
        )
        session.add(deck)
        session.flush()

        for card_payload in entry.get("cards", []):
            card = FlashcardCard(
                deck_id=deck.id,
                prompt=card_payload["prompt"],
                answer=card_payload["answer"],
                tags=card_payload.get("tags", []),
                explanation=card_payload.get("explanation"),
            )
            session.add(card)

    session.commit()


def _get_card_counts(session: Session, deck_ids: Iterable[int]) -> dict[int, int]:
    if not deck_ids:
        return {}
    statement = (
        select(FlashcardCard.deck_id, func.count(FlashcardCard.id))
        .where(FlashcardCard.deck_id.in_(list(deck_ids)))
        .group_by(FlashcardCard.deck_id)
    )
    return {deck_id: count for deck_id, count in session.exec(statement)}


def create_app(
    *,
    engine: Optional[Engine] = None,
    database: Optional[str | Path] = None,
    seed_path: Optional[Path] = None,
    use_static_pool: bool = False,
) -> FastAPI:
    """Create and configure the FastAPI flashcards application."""

    database_url = _resolve_database_url(database)
    engine_instance = engine or _create_engine(database_url, use_static_pool=use_static_pool)

    flashcard_metadata.create_all(engine_instance)

    app = FastAPI(title="MS2 Flashcards API", version="1.0.0")
    app.state.engine = engine_instance
    app.state.seed_path = seed_path or DEFAULT_SEED_PATH

    @app.on_event("startup")
    def _initialise() -> None:
        with Session(app.state.engine) as session:
            _seed_database(session, app.state.seed_path)

    def get_session() -> Generator[Session, None, None]:
        with Session(app.state.engine) as session:
            yield session

    def _get_deck(session: Session, deck_id: int) -> FlashcardDeck:
        deck = session.get(FlashcardDeck, deck_id)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")
        return deck

    def _get_card(session: Session, deck_id: int, card_id: int) -> FlashcardCard:
        card = session.get(FlashcardCard, card_id)
        if not card or card.deck_id != deck_id:
            raise HTTPException(status_code=404, detail="Card not found")
        return card

    @app.get("/decks", response_model=list[DeckSummary])
    def list_decks(
        deck_type: Optional[DeckType] = Query(default=None, description="Filter decks by type"),
        session: Session = Depends(get_session),
    ) -> list[DeckSummary]:
        statement = select(FlashcardDeck)
        if deck_type is not None:
            statement = statement.where(FlashcardDeck.deck_type == deck_type)
        statement = statement.order_by(FlashcardDeck.name)
        decks = session.exec(statement).all()
        counts = _get_card_counts(session, [deck.id for deck in decks if deck.id is not None])
        summaries = [
            DeckSummary.model_validate(
                deck,
                update={"card_count": counts.get(deck.id or 0, 0)},
            )
            for deck in decks
        ]
        return summaries

    @app.post("/decks", response_model=DeckSummary, status_code=status.HTTP_201_CREATED)
    def create_deck_endpoint(payload: DeckCreate, session: Session = Depends(get_session)) -> DeckSummary:
        deck = FlashcardDeck(**payload.model_dump())
        session.add(deck)
        session.commit()
        session.refresh(deck)
        return DeckSummary.model_validate(deck, update={"card_count": 0})

    @app.get("/decks/{deck_id}", response_model=DeckDetail)
    def get_deck(deck_id: int, session: Session = Depends(get_session)) -> DeckDetail:
        deck = _get_deck(session, deck_id)
        cards = session.exec(
            select(FlashcardCard).where(FlashcardCard.deck_id == deck_id).order_by(FlashcardCard.id)
        ).all()
        card_models = [CardRead.model_validate(card) for card in cards]
        return DeckDetail.model_validate(
            deck,
            update={"card_count": len(card_models), "cards": card_models},
        )

    @app.put("/decks/{deck_id}", response_model=DeckSummary)
    def update_deck(deck_id: int, payload: DeckUpdate, session: Session = Depends(get_session)) -> DeckSummary:
        deck = _get_deck(session, deck_id)
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            counts = _get_card_counts(session, [deck_id])
            return DeckSummary.model_validate(deck, update={"card_count": counts.get(deck_id, 0)})
        for field, value in update_data.items():
            setattr(deck, field, value)
        deck.updated_at = datetime.now(timezone.utc)
        session.add(deck)
        session.commit()
        session.refresh(deck)
        counts = _get_card_counts(session, [deck_id])
        return DeckSummary.model_validate(deck, update={"card_count": counts.get(deck_id, 0)})

    @app.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_deck(deck_id: int, session: Session = Depends(get_session)) -> None:
        deck = _get_deck(session, deck_id)
        session.exec(delete(FlashcardCard).where(FlashcardCard.deck_id == deck_id))
        session.delete(deck)
        session.commit()

    @app.get("/decks/{deck_id}/cards", response_model=list[CardRead])
    def list_cards(deck_id: int, session: Session = Depends(get_session)) -> list[CardRead]:
        _get_deck(session, deck_id)
        cards = session.exec(
            select(FlashcardCard).where(FlashcardCard.deck_id == deck_id).order_by(FlashcardCard.id)
        ).all()
        return [CardRead.model_validate(card) for card in cards]

    @app.post(
        "/decks/{deck_id}/cards",
        response_model=CardRead,
        status_code=status.HTTP_201_CREATED,
    )
    def create_card(deck_id: int, payload: CardCreate, session: Session = Depends(get_session)) -> CardRead:
        _get_deck(session, deck_id)
        card = FlashcardCard(deck_id=deck_id, **payload.model_dump())
        session.add(card)
        session.commit()
        session.refresh(card)
        return CardRead.model_validate(card)

    @app.get("/decks/{deck_id}/cards/{card_id}", response_model=CardRead)
    def get_card(deck_id: int, card_id: int, session: Session = Depends(get_session)) -> CardRead:
        card = _get_card(session, deck_id, card_id)
        return CardRead.model_validate(card)

    @app.put("/decks/{deck_id}/cards/{card_id}", response_model=CardRead)
    def update_card(
        deck_id: int,
        card_id: int,
        payload: CardUpdate,
        session: Session = Depends(get_session),
    ) -> CardRead:
        card = _get_card(session, deck_id, card_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "tags" and value is None:
                setattr(card, field, [])
            else:
                setattr(card, field, value)
        card.updated_at = datetime.now(timezone.utc)
        session.add(card)
        session.commit()
        session.refresh(card)
        return CardRead.model_validate(card)

    @app.delete("/decks/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_card(deck_id: int, card_id: int, session: Session = Depends(get_session)) -> None:
        card = _get_card(session, deck_id, card_id)
        session.delete(card)
        session.commit()

    return app

