"""Shared analytics hooks for event-driven integrations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .scheduler import AnalyticsRefreshScheduler

_DEFAULT_EVENT_LOG = Path(__file__).resolve().parents[2] / "data" / "analytics" / "events" / "assessment_completions.jsonl"


@dataclass(frozen=True)
class AssessmentCompletionEvent:
    """Structured payload describing a completed assessment."""

    assessment_id: str
    candidate_id: str
    total_questions: int
    correct_count: int
    incorrect_count: int
    omitted_count: int
    score_percent: float
    duration_seconds: Optional[int]
    completed_at: datetime
    focus_tags: Iterable[str]


class AssessmentAnalyticsHook:
    """Persist assessment completion events and request analytics refreshes."""

    def __init__(
        self,
        *,
        event_log: Path | str = _DEFAULT_EVENT_LOG,
        scheduler: Optional[AnalyticsRefreshScheduler] = None,
    ) -> None:
        self._event_log = Path(event_log)
        self._scheduler = scheduler

    def assessment_completed(self, event: AssessmentCompletionEvent) -> None:
        """Record *event* and notify the analytics scheduler."""

        payload = asdict(event)
        payload["completed_at"] = event.completed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        payload["focus_tags"] = list(event.focus_tags)
        payload["recorded_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        self._event_log.parent.mkdir(parents=True, exist_ok=True)
        with self._event_log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True))
            stream.write("\n")

        if self._scheduler is not None:
            self._scheduler.request_refresh()


__all__ = ["AssessmentAnalyticsHook", "AssessmentCompletionEvent"]
