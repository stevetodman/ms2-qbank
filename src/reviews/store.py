"""Persistence layer for question review records."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict

from .models import ReviewEvent, ReviewRecord


class ReviewStore:
    """A simple JSON-backed review store."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._lock = Lock()
        self._initialise()

    def _initialise(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"questions": {}}), encoding="utf-8")

    def _load(self) -> Dict[str, Dict[str, Dict]]:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        if "questions" not in data or not isinstance(data["questions"], dict):
            raise ValueError("Invalid review store format")
        return data

    def _save(self, data: Dict[str, Dict[str, Dict]]) -> None:
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, question_id: str) -> ReviewRecord:
        payload = self._load()["questions"].get(question_id)
        if not payload:
            return ReviewRecord(question_id=question_id)
        return ReviewRecord.from_dict(payload)

    def append(self, question_id: str, event: ReviewEvent) -> ReviewRecord:
        with self._lock:
            data = self._load()
            questions = data.setdefault("questions", {})
            record_payload = questions.get(question_id)
            if not record_payload:
                record = ReviewRecord(question_id=question_id, events=[event])
            else:
                record = ReviewRecord.from_dict(record_payload)
                record.events.append(event)
            questions[question_id] = record.to_dict()
            self._save(data)
            return record
