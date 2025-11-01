"""Lightweight data store for articles and notebook entries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import Article, NotebookEntry


class LibraryStore:
    """In-memory store seeded from JSON fixtures."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._articles = {article.id: article for article in self._load_articles()}
        self._notes = {note.id: note for note in self._load_notes()}

    def _load_articles(self) -> Iterable[Article]:
        path = self._data_dir / "articles.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for record in payload:
            yield Article.model_validate(record)

    def _load_notes(self) -> Iterable[NotebookEntry]:
        path = self._data_dir / "notes.json"
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for record in payload:
            yield NotebookEntry.model_validate(record)

    # Articles -----------------------------------------------------------------
    def list_articles(self, *, query: str | None = None, tag: str | None = None) -> list[Article]:
        results = list(self._articles.values())
        if query:
            lowered = query.lower()
            results = [
                article
                for article in results
                if lowered in article.title.lower()
                or lowered in article.summary.lower()
                or lowered in article.body.lower()
            ]
        if tag:
            lowered_tag = tag.lower()
            results = [article for article in results if lowered_tag in {t.lower() for t in article.tags}]
        return sorted(results, key=lambda article: article.title)

    def get_article(self, article_id: str) -> Article:
        return self._articles[article_id]

    def set_article_bookmark(self, article_id: str, bookmarked: bool) -> Article:
        article = self._articles[article_id]
        updated = article.model_copy(update={"bookmarked": bookmarked})
        self._articles[article_id] = updated
        return updated

    def all_article_tags(self) -> list[str]:
        tags: set[str] = set()
        for article in self._articles.values():
            tags.update(article.tags)
        return sorted(tags)

    # Notes --------------------------------------------------------------------
    def list_notes(
        self,
        *,
        query: str | None = None,
        tag: str | None = None,
        article_id: str | None = None,
        question_id: str | None = None,
    ) -> list[NotebookEntry]:
        results = list(self._notes.values())
        if query:
            lowered = query.lower()
            results = [
                note
                for note in results
                if lowered in note.title.lower() or lowered in note.body.lower()
            ]
        if tag:
            lowered_tag = tag.lower()
            results = [note for note in results if lowered_tag in {t.lower() for t in note.tags}]
        if article_id:
            results = [note for note in results if article_id in note.article_ids]
        if question_id:
            results = [note for note in results if question_id in note.question_ids]
        return sorted(results, key=lambda note: note.title)

    def get_note(self, note_id: str) -> NotebookEntry:
        return self._notes[note_id]

    def create_note(
        self,
        *,
        title: str,
        body: str,
        tags: list[str] | None = None,
        article_ids: list[str] | None = None,
        question_ids: list[str] | None = None,
    ) -> NotebookEntry:
        note_id = f"note-{uuid4().hex[:8]}"
        note = NotebookEntry(
            id=note_id,
            title=title,
            body=body,
            tags=tags or [],
            article_ids=article_ids or [],
            question_ids=question_ids or [],
            bookmarked=False,
        )
        self._notes[note.id] = note
        return note

    def update_note(self, note_id: str, **fields: object) -> NotebookEntry:
        note = self._notes[note_id]
        updated = note.model_copy(update={k: v for k, v in fields.items() if v is not None})
        self._notes[note_id] = updated
        return updated

    def set_note_bookmark(self, note_id: str, bookmarked: bool) -> NotebookEntry:
        note = self._notes[note_id]
        updated = note.model_copy(update={"bookmarked": bookmarked})
        self._notes[note_id] = updated
        return updated

    def link_note_to_question(self, note_id: str, question_id: str) -> NotebookEntry:
        note = self._notes[note_id]
        if question_id in note.question_ids:
            return note
        updated_ids = list(note.question_ids) + [question_id]
        updated = note.model_copy(update={"question_ids": updated_ids})
        self._notes[note_id] = updated
        return updated

    def all_note_tags(self) -> list[str]:
        tags: set[str] = set()
        for note in self._notes.values():
            tags.update(note.tags)
        return sorted(tags)
