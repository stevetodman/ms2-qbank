"""FastAPI application for database-backed medical library and notebook."""

import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from users.auth import decode_access_token
from .db_store import LibraryDatabaseStore
from .db_models import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    BookmarkRequest,
    BookmarkResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="MS2 QBank Medical Library API",
    description="Database-backed medical library and notebook service",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize store
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "library.db"

store = LibraryDatabaseStore(db_path=str(DB_PATH))


def optional_auth(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """Optional authentication - returns user_id if token present, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_access_token(token)
        return payload.get("user_id")
    except Exception:
        return None


# Article Endpoints
@app.post("/articles", response_model=ArticleResponse)
async def create_article(article: ArticleCreate) -> ArticleResponse:
    """Create a new article."""
    try:
        created = store.create_article(
            article_id=article.article_id,
            title=article.title,
            summary=article.summary,
            body=article.body,
            tags=article.tags,
            author=article.author,
        )

        return ArticleResponse(
            id=created.article_id,
            title=created.title,
            summary=created.summary,
            body=created.body,
            tags=json.loads(created.tags),
            bookmarked=created.bookmarked,
            author=created.author,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articles", response_model=list[ArticleResponse])
async def list_articles(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    bookmarked_only: bool = False,
) -> list[ArticleResponse]:
    """List articles with optional filtering."""
    try:
        articles = store.list_articles(query=query, tag=tag, bookmarked_only=bookmarked_only)

        return [
            ArticleResponse(
                id=a.article_id,
                title=a.title,
                summary=a.summary,
                body=a.body,
                tags=json.loads(a.tags),
                bookmarked=a.bookmarked,
                author=a.author,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in articles
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articles/tags", response_model=list[str])
async def get_article_tags() -> list[str]:
    """Get all unique article tags."""
    try:
        return store.all_article_tags()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str) -> ArticleResponse:
    """Get a single article."""
    try:
        article = store.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return ArticleResponse(
            id=article.article_id,
            title=article.title,
            summary=article.summary,
            body=article.body,
            tags=json.loads(article.tags),
            bookmarked=article.bookmarked,
            author=article.author,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, update: ArticleUpdate) -> ArticleResponse:
    """Update an article."""
    try:
        updated = store.update_article(
            article_id=article_id,
            title=update.title,
            summary=update.summary,
            body=update.body,
            tags=update.tags,
            author=update.author,
        )

        return ArticleResponse(
            id=updated.article_id,
            title=updated.title,
            summary=updated.summary,
            body=updated.body,
            tags=json.loads(updated.tags),
            bookmarked=updated.bookmarked,
            author=updated.author,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Article not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/articles/{article_id}/bookmark", response_model=BookmarkResponse)
async def bookmark_article(article_id: str, request: BookmarkRequest) -> BookmarkResponse:
    """Update article bookmark status."""
    try:
        updated = store.set_article_bookmark(article_id, request.bookmarked)
        return BookmarkResponse(id=updated.article_id, bookmarked=updated.bookmarked)
    except KeyError:
        raise HTTPException(status_code=404, detail="Article not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/articles/{article_id}")
async def delete_article(article_id: str) -> dict:
    """Delete an article."""
    try:
        deleted = store.delete_article(article_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Article not found")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Notebook Endpoints
@app.post("/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    note: NoteCreate, user_id: Optional[int] = Depends(optional_auth)
) -> NoteResponse:
    """Create a new notebook entry."""
    try:
        created = store.create_note(
            title=note.title,
            body=note.body,
            tags=note.tags,
            article_ids=note.article_ids,
            question_ids=note.question_ids,
            video_ids=note.video_ids,
            user_id=user_id,
        )

        return NoteResponse(
            id=created.note_id,
            title=created.title,
            body=created.body,
            tags=json.loads(created.tags),
            article_ids=json.loads(created.article_ids),
            question_ids=json.loads(created.question_ids),
            video_ids=json.loads(created.video_ids),
            bookmarked=created.bookmarked,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes", response_model=list[NoteResponse])
async def list_notes(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    article_id: Optional[str] = None,
    question_id: Optional[str] = None,
    video_id: Optional[str] = None,
    bookmarked_only: bool = False,
    user_id: Optional[int] = Depends(optional_auth),
) -> list[NoteResponse]:
    """List notebook entries with optional filtering."""
    try:
        notes = store.list_notes(
            query=query,
            tag=tag,
            article_id=article_id,
            question_id=question_id,
            video_id=video_id,
            user_id=user_id,
            bookmarked_only=bookmarked_only,
        )

        return [
            NoteResponse(
                id=n.note_id,
                title=n.title,
                body=n.body,
                tags=json.loads(n.tags),
                article_ids=json.loads(n.article_ids),
                question_ids=json.loads(n.question_ids),
                video_ids=json.loads(n.video_ids),
                bookmarked=n.bookmarked,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in notes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/tags", response_model=list[str])
async def get_note_tags() -> list[str]:
    """Get all unique note tags."""
    try:
        return store.all_note_tags()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str) -> NoteResponse:
    """Get a single notebook entry."""
    try:
        note = store.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        return NoteResponse(
            id=note.note_id,
            title=note.title,
            body=note.body,
            tags=json.loads(note.tags),
            article_ids=json.loads(note.article_ids),
            question_ids=json.loads(note.question_ids),
            video_ids=json.loads(note.video_ids),
            bookmarked=note.bookmarked,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, update: NoteUpdate) -> NoteResponse:
    """Update a notebook entry."""
    try:
        updated = store.update_note(
            note_id=note_id,
            title=update.title,
            body=update.body,
            tags=update.tags,
            article_ids=update.article_ids,
            question_ids=update.question_ids,
            video_ids=update.video_ids,
        )

        return NoteResponse(
            id=updated.note_id,
            title=updated.title,
            body=updated.body,
            tags=json.loads(updated.tags),
            article_ids=json.loads(updated.article_ids),
            question_ids=json.loads(updated.question_ids),
            video_ids=json.loads(updated.video_ids),
            bookmarked=updated.bookmarked,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notes/{note_id}/bookmark", response_model=BookmarkResponse)
async def bookmark_note(note_id: str, request: BookmarkRequest) -> BookmarkResponse:
    """Update note bookmark status."""
    try:
        updated = store.set_note_bookmark(note_id, request.bookmarked)
        return BookmarkResponse(id=updated.note_id, bookmarked=updated.bookmarked)
    except KeyError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/notes/{note_id}")
async def delete_note(note_id: str) -> dict:
    """Delete a notebook entry."""
    try:
        deleted = store.delete_note(note_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Note not found")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "medical-library-db"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8004)
