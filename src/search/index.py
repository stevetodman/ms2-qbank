"""Question search utilities leveraging question metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set

WordSet = Set[str]
MetadataIndex = Dict[str, WordSet]

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _normalise_scalar(value: Any) -> str:
    """Return a casefolded string representation of *value*."""

    if isinstance(value, str):
        return value.casefold().strip()
    return str(value).casefold().strip()


def _tokenise(text: str) -> WordSet:
    """Split *text* into lowercase tokens."""

    return {_normalise_scalar(token) for token in _WORD_RE.findall(text)}


def _iter_strings(value: Any) -> Iterator[str]:
    """Yield all string-like leaf values contained within *value*."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for item in value:
            yield from _iter_strings(item)
    elif value is not None:
        yield str(value)


def _normalise_tag(value: str) -> str:
    return _normalise_scalar(value)


def _normalise_tag_iter(values: Optional[Iterable[str]]) -> WordSet:
    if not values:
        return set()
    return {_normalise_tag(value) for value in values}


def _index_metadata(metadata: Mapping[str, Any]) -> MetadataIndex:
    index: MetadataIndex = {}
    for key, raw_value in metadata.items():
        values = {_normalise_scalar(item) for item in _iter_strings(raw_value)}
        if values:
            index[key.casefold()] = values
    return index


def _normalise_metadata_filters(filters: Optional[Mapping[str, Any]]) -> MetadataIndex:
    if not filters:
        return {}

    normalised: MetadataIndex = {}
    for key, raw_value in filters.items():
        if isinstance(raw_value, Mapping):
            values = {_normalise_scalar(item) for item in raw_value.values()}
        elif isinstance(raw_value, Sequence) and not isinstance(raw_value, (bytes, bytearray, str)):
            values = {_normalise_scalar(item) for item in raw_value}
        else:
            values = {_normalise_scalar(raw_value)}
        if values:
            normalised[key.casefold()] = values
    return normalised


@dataclass(frozen=True)
class QuestionRecord:
    """A single question enriched with search metadata."""

    raw: Mapping[str, Any]
    search_tokens: WordSet
    tags: WordSet
    metadata_index: MetadataIndex

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "QuestionRecord":
        search_tokens: WordSet = set()
        tags: WordSet = set()

        question_id = payload.get("id")
        if isinstance(question_id, str):
            search_tokens.update(_tokenise(question_id))

        stem = payload.get("stem")
        if isinstance(stem, str):
            search_tokens.update(_tokenise(stem))

        choices = payload.get("choices")
        if isinstance(choices, Sequence) and not isinstance(choices, (bytes, bytearray, str)):
            for choice in choices:
                if isinstance(choice, Mapping):
                    label = choice.get("label")
                    if isinstance(label, str):
                        search_tokens.update(_tokenise(label))
                    text = choice.get("text")
                    if isinstance(text, str):
                        search_tokens.update(_tokenise(text))

        explanation = payload.get("explanation")
        if isinstance(explanation, Mapping):
            summary = explanation.get("summary")
            if isinstance(summary, str):
                search_tokens.update(_tokenise(summary))
            rationales = explanation.get("rationales")
            if isinstance(rationales, Sequence) and not isinstance(rationales, (bytes, bytearray, str)):
                for rationale in rationales:
                    if isinstance(rationale, Mapping):
                        rationale_text = rationale.get("text")
                        if isinstance(rationale_text, str):
                            search_tokens.update(_tokenise(rationale_text))
                        rationale_choice = rationale.get("choice")
                        if isinstance(rationale_choice, str):
                            search_tokens.update(_tokenise(rationale_choice))

        tags_value = payload.get("tags")
        if isinstance(tags_value, Sequence) and not isinstance(tags_value, (bytes, bytearray, str)):
            tags = {_normalise_tag(tag) for tag in tags_value if isinstance(tag, str)}
            search_tokens.update(tags)

        metadata_value = payload.get("metadata")
        metadata_index: MetadataIndex = {}
        if isinstance(metadata_value, Mapping):
            metadata_index = _index_metadata(metadata_value)
            for string_value in _iter_strings(metadata_value):
                search_tokens.add(_normalise_scalar(string_value))
                search_tokens.update(_tokenise(string_value))

        answer = payload.get("answer")
        if isinstance(answer, str):
            search_tokens.update(_tokenise(answer))

        return cls(payload, search_tokens, tags, metadata_index)

    def matches_tags(self, requested: WordSet) -> bool:
        if not requested:
            return True
        return requested.issubset(self.tags)

    def matches_metadata(self, filters: MetadataIndex) -> bool:
        if not filters:
            return True
        for key, expected in filters.items():
            values = self.metadata_index.get(key)
            if not values or values.isdisjoint(expected):
                return False
        return True

    def matches_query(self, tokens: WordSet) -> bool:
        if not tokens:
            return True
        return tokens.issubset(self.search_tokens)


class QuestionIndex:
    """Full-text search helper for question datasets."""

    def __init__(self, questions: Iterable[Mapping[str, Any]]):
        self._records: List[QuestionRecord] = [QuestionRecord.from_mapping(item) for item in questions]

    def search(
        self,
        query: Optional[str] = None,
        *,
        tags: Optional[Iterable[str]] = None,
        metadata_filters: Optional[Mapping[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Mapping[str, Any]]:
        query_tokens = _tokenise(query) if isinstance(query, str) else set()
        tag_filters = _normalise_tag_iter(tags)
        metadata_filter_values = _normalise_metadata_filters(metadata_filters)

        matches: List[Mapping[str, Any]] = []
        for record in self._records:
            if not record.matches_query(query_tokens):
                continue
            if not record.matches_tags(tag_filters):
                continue
            if not record.matches_metadata(metadata_filter_values):
                continue
            matches.append(record.raw)
            if limit is not None and len(matches) >= limit:
                break
        return matches

    def add(self, question: Mapping[str, Any]) -> None:
        """Add a single *question* to the index."""

        self._records.append(QuestionRecord.from_mapping(question))

    def all(self) -> List[Mapping[str, Any]]:
        """Return all indexed question payloads."""

        return [record.raw for record in self._records]
