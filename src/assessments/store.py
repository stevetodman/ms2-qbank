"""In-memory persistence and scoring utilities for assessments."""

from __future__ import annotations

import itertools
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping, Optional

from analytics.hooks import AssessmentAnalyticsHook, AssessmentCompletionEvent
from .models import (
    AssessmentBlueprint,
    AssessmentQuestion,
    AssessmentScoreBreakdown,
    ChoicePayload,
)


@dataclass
class AssessmentRecord:
    """Internal state container for an assessment lifecycle."""

    blueprint: AssessmentBlueprint
    question_payloads: list[dict]
    status: str = "created"
    assessment_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    responses: dict[str, Optional[str]] = field(default_factory=dict)
    score: Optional[AssessmentScoreBreakdown] = None


class AssessmentStore:
    """Thread-safe in-memory store coordinating assessments."""

    def __init__(
        self,
        questions: Iterable[Mapping[str, object]],
        *,
        question_count: int = 160,
        analytics_hook: Optional[AssessmentAnalyticsHook] = None,
    ) -> None:
        self._questions = [dict(question) for question in questions]
        if not self._questions:
            raise ValueError("At least one question is required to seed assessments")
        self._question_count = max(1, int(question_count))
        self._analytics_hook = analytics_hook
        self._records: dict[str, AssessmentRecord] = {}
        self._lock = threading.Lock()

    @property
    def question_count(self) -> int:
        return self._question_count

    def create(self, blueprint: AssessmentBlueprint) -> AssessmentRecord:
        with self._lock:
            record = AssessmentRecord(blueprint=blueprint, question_payloads=self._questions)
            self._records[record.assessment_id] = record
            return record

    def start(self, assessment_id: str) -> AssessmentRecord:
        with self._lock:
            record = self._get_record_locked(assessment_id)
            if record.status not in {"created", "ready"}:
                raise ValueError("Assessment cannot be started in its current state")
            selected = self._select_questions(record)
            record.question_payloads = selected
            record.status = "in-progress"
            record.started_at = datetime.now(timezone.utc)
            duration = timedelta(minutes=record.blueprint.time_limit_minutes)
            record.expires_at = record.started_at + duration if duration.total_seconds() > 0 else None
            record.responses = {}
            record.score = None
            record.submitted_at = None
            return record

    def submit(self, assessment_id: str, responses: Mapping[str, Optional[str]]) -> AssessmentRecord:
        with self._lock:
            record = self._get_record_locked(assessment_id)
            if record.status != "in-progress" or not record.started_at:
                raise ValueError("Assessment must be started before submission")

            canonical_responses: dict[str, Optional[str]] = {}
            for question in record.question_payloads:
                qid = question.get("id")
                if not isinstance(qid, str):
                    continue
                canonical_responses[qid] = responses.get(qid)
            record.responses = canonical_responses
            record.submitted_at = datetime.now(timezone.utc)
            record.status = "completed"
            record.score = self._score(record)

            if self._analytics_hook is not None:
                focus_tags = record.blueprint.tags or []
                duration_seconds: Optional[int]
                if record.started_at and record.submitted_at:
                    duration_seconds = int((record.submitted_at - record.started_at).total_seconds())
                else:
                    duration_seconds = None
                event = AssessmentCompletionEvent(
                    assessment_id=record.assessment_id,
                    candidate_id=record.blueprint.candidate_id,
                    total_questions=record.score.total_questions,
                    correct_count=record.score.correct,
                    incorrect_count=record.score.incorrect,
                    omitted_count=record.score.omitted,
                    score_percent=record.score.percentage,
                    duration_seconds=duration_seconds,
                    completed_at=record.submitted_at or datetime.now(timezone.utc),
                    focus_tags=focus_tags,
                )
                self._analytics_hook.assessment_completed(event)

            return record

    def get(self, assessment_id: str) -> AssessmentRecord:
        with self._lock:
            return self._get_record_locked(assessment_id)

    def _get_record_locked(self, assessment_id: str) -> AssessmentRecord:
        try:
            return self._records[assessment_id]
        except KeyError as exc:
            raise KeyError(f"Assessment '{assessment_id}' was not found") from exc

    def _select_questions(self, record: AssessmentRecord) -> list[dict]:
        candidates = self._filter_questions(record.blueprint)
        if not candidates:
            raise ValueError("No questions match the requested filters")

        selected: list[dict] = []
        iterator = itertools.cycle(candidates)
        for index in range(self._question_count):
            original = dict(next(iterator))
            source_id = original.get("id")
            if isinstance(source_id, str):
                delivery_id = f"{source_id}__{index + 1}"
            else:
                delivery_id = f"question__{index + 1}"
            original.setdefault("_source_id", source_id)
            original["id"] = delivery_id
            selected.append(original)
        return selected

    def _filter_questions(self, blueprint: AssessmentBlueprint) -> list[dict]:
        filtered: list[dict] = []
        for payload in self._questions:
            metadata = payload.get("metadata") if isinstance(payload, Mapping) else {}
            tags = payload.get("tags") if isinstance(payload, Mapping) else []
            if blueprint.subject and metadata.get("subject") != blueprint.subject:
                continue
            if blueprint.system and metadata.get("system") != blueprint.system:
                continue
            if blueprint.difficulty and metadata.get("difficulty") != blueprint.difficulty:
                continue
            if blueprint.tags:
                payload_tags = set(tag for tag in tags if isinstance(tag, str))
                if not set(blueprint.tags).issubset(payload_tags):
                    continue
            filtered.append(dict(payload))
        return filtered

    def _score(self, record: AssessmentRecord) -> AssessmentScoreBreakdown:
        total = len(record.question_payloads)
        correct = 0
        answered = 0
        for question in record.question_payloads:
            qid = question.get("id")
            correct_answer = question.get("answer")
            if not isinstance(qid, str) or not isinstance(correct_answer, str):
                continue
            selected = record.responses.get(qid)
            if selected:
                answered += 1
                if selected == correct_answer:
                    correct += 1
        incorrect = answered - correct
        omitted = total - answered
        percentage = 0.0 if total == 0 else round((correct / total) * 100, 2)

        duration_seconds: Optional[int] = None
        if record.started_at and record.submitted_at:
            duration_seconds = int((record.submitted_at - record.started_at).total_seconds())

        return AssessmentScoreBreakdown(
            total_questions=total,
            correct=correct,
            incorrect=incorrect,
            omitted=omitted,
            percentage=percentage,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def question_payload(record: AssessmentRecord) -> list[AssessmentQuestion]:
        questions: list[AssessmentQuestion] = []
        for payload in record.question_payloads:
            qid = payload.get("id")
            stem = payload.get("stem")
            choices = payload.get("choices")
            if not isinstance(qid, str) or not isinstance(stem, str) or not isinstance(choices, list):
                continue
            choice_payloads = [
                ChoicePayload(label=str(choice.get("label")), text=str(choice.get("text")))
                for choice in choices
                if isinstance(choice, Mapping) and "label" in choice and "text" in choice
            ]
            questions.append(AssessmentQuestion(id=qid, stem=stem, choices=choice_payloads))
        return questions


__all__ = ["AssessmentStore", "AssessmentRecord"]
