"""Domain models for question reviews."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterable, List, Optional


class InvalidTransitionError(ValueError):
    """Raised when an invalid review status transition is requested."""


class ReviewerRole(str, Enum):
    """Supported reviewer roles for workflow decisions."""

    AUTHOR = "author"
    REVIEWER = "reviewer"
    EDITOR = "editor"
    ADMIN = "admin"

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
    role: ReviewerRole
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "reviewer": self.reviewer,
            "action": self.action.value,
            "role": self.role.value,
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
        role_raw = payload.get("role", ReviewerRole.REVIEWER.value)
        role = ReviewerRole(role_raw)
        return cls(reviewer=reviewer, action=action, role=role, comment=comment, timestamp=timestamp)


@dataclass
class ReviewRecord:
    """A review ledger for a specific question."""

    question_id: str
    events: List[ReviewEvent] = field(default_factory=list)

    _STATUS_PENDING = "pending"
    _STATUS_APPROVED = "approved"
    _STATUS_REJECTED = "rejected"

    _TRANSITIONS = {
        _STATUS_PENDING: {
            ReviewAction.COMMENT: _STATUS_PENDING,
            ReviewAction.APPROVE: _STATUS_APPROVED,
            ReviewAction.REJECT: _STATUS_REJECTED,
        },
        _STATUS_APPROVED: {
            ReviewAction.COMMENT: _STATUS_APPROVED,
        },
        _STATUS_REJECTED: {
            ReviewAction.COMMENT: _STATUS_REJECTED,
        },
    }

    def current_status(self) -> str:
        status = self._STATUS_PENDING
        for event in self.events:
            if event.action is ReviewAction.APPROVE:
                status = self._STATUS_APPROVED
            elif event.action is ReviewAction.REJECT:
                status = self._STATUS_REJECTED
        return status

    def apply_event(self, event: ReviewEvent) -> str:
        """Apply *event* to the record enforcing status transitions.

        Returns the resulting status after applying the event.
        """

        current_status = self.current_status()
        next_status = self._next_status(current_status, event.action)
        self.events.append(event)
        return next_status

    def _next_status(self, current_status: str, action: ReviewAction) -> str:
        transitions = self._TRANSITIONS.get(current_status, {})
        if action not in transitions:
            raise InvalidTransitionError(
                f"Cannot apply action '{action.value}' when review is {current_status}."
            )
        return transitions[action]

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
