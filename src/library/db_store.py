"""Database-backed store for medical library and notebook."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Session, SQLModel, create_engine, select, or_

from .db_models import ArticleDB, NotebookEntryDB, ArticleResponse, NoteResponse


class LibraryDatabaseStore:
    """Database-backed store for articles and notebook entries."""

    def __init__(self, db_path: str = "library.db"):
        """Initialize the library store with a database connection."""
        if not db_path.startswith("sqlite:///"):
            db_path = f"sqlite:///{db_path}"

        self.engine = create_engine(db_path, echo=False)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        from .db_models import ArticleDB, NotebookEntryDB
        SQLModel.metadata.create_all(self.engine)

    # Articles
    def create_article(
        self,
        article_id: str,
        title: str,
        summary: str,
        body: str,
        tags: list[str] = None,
        author: Optional[str] = None,
    ) -> ArticleDB:
        """Create a new article."""
        now = datetime.now(timezone.utc)
        article = ArticleDB(
            article_id=article_id,
            title=title,
            summary=summary,
            body=body,
            tags=json.dumps(tags or []),
            author=author,
            bookmarked=False,
            created_at=now,
            updated_at=now,
        )

        with Session(self.engine) as session:
            session.add(article)
            session.commit()
            session.refresh(article)

        return article

    def get_article(self, article_id: str) -> Optional[ArticleDB]:
        """Retrieve an article by ID."""
        with Session(self.engine) as session:
            statement = select(ArticleDB).where(ArticleDB.article_id == article_id)
            return session.exec(statement).first()

    def list_articles(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        bookmarked_only: bool = False,
    ) -> List[ArticleDB]:
        """List articles with optional filtering."""
        with Session(self.engine) as session:
            statement = select(ArticleDB)

            if bookmarked_only:
                statement = statement.where(ArticleDB.bookmarked == True)

            articles = list(session.exec(statement).all())

            # Apply text search filter
            if query:
                query_lower = query.lower()
                articles = [
                    a for a in articles
                    if query_lower in a.title.lower()
                    or query_lower in a.summary.lower()
                    or query_lower in a.body.lower()
                ]

            # Apply tag filter
            if tag:
                tag_lower = tag.lower()
                filtered = []
                for article in articles:
                    article_tags = json.loads(article.tags)
                    if any(tag_lower == t.lower() for t in article_tags):
                        filtered.append(article)
                articles = filtered

            return sorted(articles, key=lambda a: a.title)

    def update_article(
        self,
        article_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        body: Optional[str] = None,
        tags: Optional[list[str]] = None,
        author: Optional[str] = None,
    ) -> ArticleDB:
        """Update an article."""
        with Session(self.engine) as session:
            statement = select(ArticleDB).where(ArticleDB.article_id == article_id)
            article = session.exec(statement).first()

            if not article:
                raise KeyError(f"Article '{article_id}' not found")

            if title is not None:
                article.title = title
            if summary is not None:
                article.summary = summary
            if body is not None:
                article.body = body
            if tags is not None:
                article.tags = json.dumps(tags)
            if author is not None:
                article.author = author

            article.updated_at = datetime.now(timezone.utc)

            session.add(article)
            session.commit()
            session.refresh(article)

        return article

    def set_article_bookmark(self, article_id: str, bookmarked: bool) -> ArticleDB:
        """Set article bookmark status."""
        with Session(self.engine) as session:
            statement = select(ArticleDB).where(ArticleDB.article_id == article_id)
            article = session.exec(statement).first()

            if not article:
                raise KeyError(f"Article '{article_id}' not found")

            article.bookmarked = bookmarked
            article.updated_at = datetime.now(timezone.utc)

            session.add(article)
            session.commit()
            session.refresh(article)

        return article

    def delete_article(self, article_id: str) -> bool:
        """Delete an article."""
        with Session(self.engine) as session:
            statement = select(ArticleDB).where(ArticleDB.article_id == article_id)
            article = session.exec(statement).first()

            if not article:
                return False

            session.delete(article)
            session.commit()
            return True

    def all_article_tags(self) -> List[str]:
        """Get all unique article tags."""
        with Session(self.engine) as session:
            articles = list(session.exec(select(ArticleDB)).all())

        tags_set = set()
        for article in articles:
            article_tags = json.loads(article.tags)
            tags_set.update(article_tags)

        return sorted(tags_set)

    # Notebook Entries
    def create_note(
        self,
        title: str,
        body: str,
        tags: list[str] = None,
        article_ids: list[str] = None,
        question_ids: list[str] = None,
        video_ids: list[str] = None,
        user_id: Optional[int] = None,
    ) -> NotebookEntryDB:
        """Create a new notebook entry."""
        now = datetime.now(timezone.utc)
        note = NotebookEntryDB(
            note_id=uuid.uuid4().hex,
            user_id=user_id,
            title=title,
            body=body,
            tags=json.dumps(tags or []),
            article_ids=json.dumps(article_ids or []),
            question_ids=json.dumps(question_ids or []),
            video_ids=json.dumps(video_ids or []),
            bookmarked=False,
            created_at=now,
            updated_at=now,
        )

        with Session(self.engine) as session:
            session.add(note)
            session.commit()
            session.refresh(note)

        return note

    def get_note(self, note_id: str) -> Optional[NotebookEntryDB]:
        """Retrieve a note by ID."""
        with Session(self.engine) as session:
            statement = select(NotebookEntryDB).where(NotebookEntryDB.note_id == note_id)
            return session.exec(statement).first()

    def list_notes(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        article_id: Optional[str] = None,
        question_id: Optional[str] = None,
        video_id: Optional[str] = None,
        user_id: Optional[int] = None,
        bookmarked_only: bool = False,
    ) -> List[NotebookEntryDB]:
        """List notes with optional filtering."""
        with Session(self.engine) as session:
            statement = select(NotebookEntryDB)

            if user_id is not None:
                statement = statement.where(NotebookEntryDB.user_id == user_id)

            if bookmarked_only:
                statement = statement.where(NotebookEntryDB.bookmarked == True)

            notes = list(session.exec(statement).all())

            # Apply text search filter
            if query:
                query_lower = query.lower()
                notes = [
                    n for n in notes
                    if query_lower in n.title.lower() or query_lower in n.body.lower()
                ]

            # Apply tag filter
            if tag:
                tag_lower = tag.lower()
                filtered = []
                for note in notes:
                    note_tags = json.loads(note.tags)
                    if any(tag_lower == t.lower() for t in note_tags):
                        filtered.append(note)
                notes = filtered

            # Apply article_id filter
            if article_id:
                filtered = []
                for note in notes:
                    note_article_ids = json.loads(note.article_ids)
                    if article_id in note_article_ids:
                        filtered.append(note)
                notes = filtered

            # Apply question_id filter
            if question_id:
                filtered = []
                for note in notes:
                    note_question_ids = json.loads(note.question_ids)
                    if question_id in note_question_ids:
                        filtered.append(note)
                notes = filtered

            # Apply video_id filter
            if video_id:
                filtered = []
                for note in notes:
                    note_video_ids = json.loads(note.video_ids)
                    if video_id in note_video_ids:
                        filtered.append(note)
                notes = filtered

            return sorted(notes, key=lambda n: n.created_at, reverse=True)

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        tags: Optional[list[str]] = None,
        article_ids: Optional[list[str]] = None,
        question_ids: Optional[list[str]] = None,
        video_ids: Optional[list[str]] = None,
    ) -> NotebookEntryDB:
        """Update a notebook entry."""
        with Session(self.engine) as session:
            statement = select(NotebookEntryDB).where(NotebookEntryDB.note_id == note_id)
            note = session.exec(statement).first()

            if not note:
                raise KeyError(f"Note '{note_id}' not found")

            if title is not None:
                note.title = title
            if body is not None:
                note.body = body
            if tags is not None:
                note.tags = json.dumps(tags)
            if article_ids is not None:
                note.article_ids = json.dumps(article_ids)
            if question_ids is not None:
                note.question_ids = json.dumps(question_ids)
            if video_ids is not None:
                note.video_ids = json.dumps(video_ids)

            note.updated_at = datetime.now(timezone.utc)

            session.add(note)
            session.commit()
            session.refresh(note)

        return note

    def set_note_bookmark(self, note_id: str, bookmarked: bool) -> NotebookEntryDB:
        """Set note bookmark status."""
        with Session(self.engine) as session:
            statement = select(NotebookEntryDB).where(NotebookEntryDB.note_id == note_id)
            note = session.exec(statement).first()

            if not note:
                raise KeyError(f"Note '{note_id}' not found")

            note.bookmarked = bookmarked
            note.updated_at = datetime.now(timezone.utc)

            session.add(note)
            session.commit()
            session.refresh(note)

        return note

    def delete_note(self, note_id: str) -> bool:
        """Delete a notebook entry."""
        with Session(self.engine) as session:
            statement = select(NotebookEntryDB).where(NotebookEntryDB.note_id == note_id)
            note = session.exec(statement).first()

            if not note:
                return False

            session.delete(note)
            session.commit()
            return True

    def all_note_tags(self) -> List[str]:
        """Get all unique note tags."""
        with Session(self.engine) as session:
            notes = list(session.exec(select(NotebookEntryDB)).all())

        tags_set = set()
        for note in notes:
            note_tags = json.loads(note.tags)
            tags_set.update(note_tags)

        return sorted(tags_set)


__all__ = ["LibraryDatabaseStore"]
