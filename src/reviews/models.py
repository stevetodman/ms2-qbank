"""Domain models for question reviews."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterable, List, Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class ReviewAction(str, Enum):
    """Supported actions reviewers can take on a question."""

    APPROVE = "approve"
    REJECT = "reject"
    COMMENT = "comment"


@dataclass
class ReviewEvent:
    """A single review action with optional context."""

    reviewer: str
    action: ReviewAction
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "reviewer": self.reviewer,
            "action": self.action.value,
            "timestamp": self.timestamp.strftime(ISO_FORMAT),
        }
        if self.comment is not None:
            payload["comment"] = self.comment
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, str]) -> "ReviewEvent":
        timestamp_raw = payload.get("timestamp")
        timestamp = datetime.strptime(timestamp_raw, ISO_FORMAT).replace(tzinfo=timezone.utc)
        comment = payload.get("comment")
        action = ReviewAction(payload["action"])
        reviewer = payload["reviewer"]
        return cls(reviewer=reviewer, action=action, comment=comment, timestamp=timestamp)


@dataclass
class ReviewRecord:
    """A review ledger for a specific question."""

    question_id: str
    events: List[ReviewEvent] = field(default_factory=list)

    def current_status(self) -> str:
        status = "pending"
        for event in self.events:
            if event.action is ReviewAction.APPROVE:
                status = "approved"
            elif event.action is ReviewAction.REJECT:
                status = "rejected"
        return status

    def to_dict(self) -> Dict[str, Iterable[Dict[str, str]]]:
        return {
            "question_id": self.question_id,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Iterable[Dict[str, str]]]) -> "ReviewRecord":
        question_id = payload["question_id"]
        events_payload = payload.get("events", [])
        events = [ReviewEvent.from_dict(event) for event in events_payload]
        return cls(question_id=question_id, events=events)
