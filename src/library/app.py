"""FastAPI application exposing the medical library and notebook APIs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException

from logging_config import configure_logging, get_logger, RequestLoggingMiddleware

from .models import (
    Article,
    ArticleQuery,
    BookmarkRequest,
    BookmarkResponse,
    CreateNoteRequest,
    LinkReviewRequest,
    NoteQuery,
    NotebookEntry,
    UpdateNoteRequest,
)
from .store import LibraryStore

# Configure structured logging
configure_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    service_name="library-api",
    json_format=(os.getenv("LOG_FORMAT", "json") == "json"),
)

logger = get_logger(__name__)

DEFAULT_DATA_DIR = Path("data/library")


def _create_store(data_dir: Optional[Path] = None) -> LibraryStore:
    base_dir = data_dir or DEFAULT_DATA_DIR
    if not base_dir.exists():
        raise RuntimeError(f"Library data directory not found: {base_dir}")
    return LibraryStore(base_dir)


def create_app(*, store: Optional[LibraryStore] = None, data_dir: Optional[Path] = None) -> FastAPI:
    """Instantiate the FastAPI app with configured dependencies."""

    app = FastAPI(title="MS2 QBank Library API", version="1.0.0")

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    app.state.library_store = store or _create_store(data_dir)

    logger.info("Library API initialized")

    def get_store() -> LibraryStore:
        return app.state.library_store

    # Article endpoints --------------------------------------------------------
    @app.get("/articles", response_model=list[Article])
    def list_articles(params: ArticleQuery = Depends(), store: LibraryStore = Depends(get_store)) -> list[Article]:
        return store.list_articles(query=params.query, tag=params.tag)

    @app.get("/articles/tags", response_model=list[str])
    def get_article_tags(store: LibraryStore = Depends(get_store)) -> list[str]:
        return store.all_article_tags()

    @app.get("/articles/{article_id}", response_model=Article)
    def get_article(article_id: str, store: LibraryStore = Depends(get_store)) -> Article:
        try:
            return store.get_article(article_id)
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Article not found") from exc

    @app.post("/articles/{article_id}/bookmark", response_model=BookmarkResponse)
    def bookmark_article(
        article_id: str,
        payload: BookmarkRequest,
        store: LibraryStore = Depends(get_store),
    ) -> BookmarkResponse:
        try:
            article = store.set_article_bookmark(article_id, payload.bookmarked)
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Article not found") from exc
        return BookmarkResponse(id=article.id, bookmarked=article.bookmarked)

    # Notebook endpoints -------------------------------------------------------
    @app.get("/notes", response_model=list[NotebookEntry])
    def list_notes(params: NoteQuery = Depends(), store: LibraryStore = Depends(get_store)) -> list[NotebookEntry]:
        return store.list_notes(
            query=params.query,
            tag=params.tag,
            article_id=params.article_id,
            question_id=params.question_id,
        )

    @app.get("/notes/tags", response_model=list[str])
    def get_note_tags(store: LibraryStore = Depends(get_store)) -> list[str]:
        return store.all_note_tags()

    @app.get("/notes/{note_id}", response_model=NotebookEntry)
    def get_note(note_id: str, store: LibraryStore = Depends(get_store)) -> NotebookEntry:
        try:
            return store.get_note(note_id)
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Note not found") from exc

    @app.post("/notes", response_model=NotebookEntry, status_code=201)
    def create_note(payload: CreateNoteRequest, store: LibraryStore = Depends(get_store)) -> NotebookEntry:
        return store.create_note(
            title=payload.title,
            body=payload.body,
            tags=payload.tags,
            article_ids=payload.article_ids,
            question_ids=payload.question_ids,
        )

    @app.patch("/notes/{note_id}", response_model=NotebookEntry)
    def update_note(
        note_id: str,
        payload: UpdateNoteRequest,
        store: LibraryStore = Depends(get_store),
    ) -> NotebookEntry:
        try:
            return store.update_note(
                note_id,
                title=payload.title,
                body=payload.body,
                tags=payload.tags,
                article_ids=payload.article_ids,
                question_ids=payload.question_ids,
            )
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Note not found") from exc

    @app.post("/notes/{note_id}/bookmark", response_model=BookmarkResponse)
    def bookmark_note(
        note_id: str,
        payload: BookmarkRequest,
        store: LibraryStore = Depends(get_store),
    ) -> BookmarkResponse:
        try:
            note = store.set_note_bookmark(note_id, payload.bookmarked)
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Note not found") from exc
        return BookmarkResponse(id=note.id, bookmarked=note.bookmarked)

    @app.post("/notes/{note_id}/link-review", response_model=NotebookEntry)
    def link_note_to_review(
        note_id: str,
        payload: LinkReviewRequest,
        store: LibraryStore = Depends(get_store),
    ) -> NotebookEntry:
        try:
            return store.link_note_to_question(note_id, payload.question_id)
        except KeyError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Note not found") from exc

    return app


app = create_app()
