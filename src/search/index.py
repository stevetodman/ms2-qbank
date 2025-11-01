"""Question search utilities leveraging question metadata."""

from __future__ import annotations

import re
import json
from difflib import get_close_matches
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

WordSet = Set[str]
MetadataIndex = Dict[str, WordSet]

_INDEX_STORAGE_PATH = Path(__file__).resolve().parents[2] / "data" / "search" / "index.json"
_INDEX_STORAGE_VERSION = 1

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
        self._id_lookup: Dict[str, QuestionRecord] = {}
        self._ordered_ids: List[str] = []
        for record in self._records:
            raw_id = record.raw.get("id")
            identifier: Optional[str] = None
            if isinstance(raw_id, str):
                identifier = raw_id
            elif raw_id is not None:
                identifier = _normalise_scalar(raw_id)
            if identifier is None:
                continue
            self._id_lookup[identifier] = record
            self._ordered_ids.append(identifier)

        persisted = self._load_persisted_index()
        fingerprint = self._fingerprint()
        if persisted and persisted.get("fingerprint") == fingerprint:
            self._token_index = {
                token: set(values) for token, values in persisted.get("tokens", {}).items()
            }
            self._tag_index = {
                tag: set(values) for tag, values in persisted.get("tags", {}).items()
            }
            metadata_blob = persisted.get("metadata", {})
            self._metadata_index = {
                key: {value: set(ids) for value, ids in values.items()}
                for key, values in metadata_blob.items()
            }
            filters = persisted.get("filters", {})
            self._filter_values = {
                "subjects": list(filters.get("subjects", [])),
                "systems": list(filters.get("systems", [])),
                "statuses": list(filters.get("statuses", [])),
                "difficulties": list(filters.get("difficulties", [])),
                "tags": list(filters.get("tags", [])),
            }
        else:
            self._build_indexes()
            self._persist_index(fingerprint)

    def _fingerprint(self) -> Dict[str, Any]:
        return {
            "version": _INDEX_STORAGE_VERSION,
            "question_ids": sorted(self._ordered_ids),
            "record_count": len(self._ordered_ids),
        }

    def _load_persisted_index(self) -> Optional[Dict[str, Any]]:
        if not _INDEX_STORAGE_PATH.exists():
            return None
        try:
            with _INDEX_STORAGE_PATH.open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
        except (OSError, json.JSONDecodeError):
            return None
        if payload.get("version") != _INDEX_STORAGE_VERSION:
            return None
        return payload

    def _persist_index(self, fingerprint: Dict[str, Any]) -> None:
        data = {
            "version": _INDEX_STORAGE_VERSION,
            "fingerprint": fingerprint,
            "tokens": {token: sorted(ids) for token, ids in self._token_index.items()},
            "tags": {tag: sorted(ids) for tag, ids in self._tag_index.items()},
            "metadata": {
                key: {value: sorted(ids) for value, ids in values.items()}
                for key, values in self._metadata_index.items()
            },
            "filters": self._filter_values,
        }
        _INDEX_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _INDEX_STORAGE_PATH.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)

    def _build_indexes(self) -> None:
        self._token_index: Dict[str, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}
        self._metadata_index: Dict[str, Dict[str, Set[str]]] = {}

        subjects: Set[str] = set()
        systems: Set[str] = set()
        statuses: Set[str] = set()
        difficulties: Set[str] = set()
        tags: Set[str] = set()

        for identifier in self._ordered_ids:
            record = self._id_lookup.get(identifier)
            if record is None:
                continue

            for token in record.search_tokens:
                self._token_index.setdefault(token, set()).add(identifier)

            for tag_value in record.tags:
                self._tag_index.setdefault(tag_value, set()).add(identifier)

            for key, values in record.metadata_index.items():
                index_for_key = self._metadata_index.setdefault(key, {})
                for value in values:
                    index_for_key.setdefault(value, set()).add(identifier)

            metadata = record.raw.get("metadata", {})
            if isinstance(metadata, Mapping):
                subject = metadata.get("subject")
                if isinstance(subject, str):
                    subjects.add(subject)
                system = metadata.get("system")
                if isinstance(system, str):
                    systems.add(system)
                status = metadata.get("status")
                if isinstance(status, str):
                    statuses.add(status)
                difficulty = metadata.get("difficulty")
                if isinstance(difficulty, str):
                    difficulties.add(difficulty)

            if record.raw.get("tags"):
                for tag_label in record.raw.get("tags", []):
                    if isinstance(tag_label, str):
                        tags.add(tag_label)

        self._filter_values = {
            "subjects": sorted(subjects),
            "systems": sorted(systems),
            "statuses": sorted(statuses),
            "difficulties": sorted(difficulties),
            "tags": sorted(tags),
        }

    def _expand_query_token(self, token: str) -> Set[str]:
        candidates: Set[str] = set()
        if token in self._token_index:
            candidates.add(token)
        for known in self._token_index:
            if known.startswith(token) or token in known:
                candidates.add(known)
        fuzzy = get_close_matches(token, list(self._token_index.keys()), n=5, cutoff=0.75)
        candidates.update(fuzzy)
        return candidates

    def _resolve_query_matches(self, query_tokens: WordSet) -> Set[str]:
        if not query_tokens:
            return set(self._ordered_ids)

        candidate_ids: Optional[Set[str]] = None
        for token in query_tokens:
            expanded = self._expand_query_token(token)
            if not expanded:
                return set()
            token_matches: Set[str] = set()
            for candidate in expanded:
                token_matches.update(self._token_index.get(candidate, set()))
            if candidate_ids is None:
                candidate_ids = token_matches
            else:
                candidate_ids &= token_matches
            if not candidate_ids:
                return set()
        return candidate_ids or set()

    def _apply_tag_filters(self, candidate_ids: Set[str], tags: WordSet) -> Set[str]:
        if not tags:
            return candidate_ids
        filtered = set(candidate_ids)
        for tag in tags:
            matching = self._tag_index.get(tag)
            if not matching:
                return set()
            filtered &= matching
            if not filtered:
                return set()
        return filtered

    def _apply_metadata_filters(
        self, candidate_ids: Set[str], metadata_filters: MetadataIndex
    ) -> Set[str]:
        if not metadata_filters:
            return candidate_ids
        filtered = set(candidate_ids)
        for key, expected_values in metadata_filters.items():
            index_for_key = self._metadata_index.get(key)
            if not index_for_key:
                return set()
            matches_for_key: Set[str] = set()
            for value in expected_values:
                matches_for_key.update(index_for_key.get(value, set()))
            if not matches_for_key:
                return set()
            filtered &= matches_for_key
            if not filtered:
                return set()
        return filtered

    def search(
        self,
        query: Optional[str] = None,
        *,
        tags: Optional[Iterable[str]] = None,
        metadata_filters: Optional[Mapping[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Tuple[List[Mapping[str, Any]], int]:
        query_tokens = _tokenise(query) if isinstance(query, str) else set()
        tag_filters = _normalise_tag_iter(tags)
        metadata_filter_values = _normalise_metadata_filters(metadata_filters)

        candidate_ids = self._resolve_query_matches(query_tokens)
        if not candidate_ids:
            return [], 0

        candidate_ids = self._apply_tag_filters(candidate_ids, tag_filters)
        if not candidate_ids:
            return [], 0

        candidate_ids = self._apply_metadata_filters(candidate_ids, metadata_filter_values)
        if not candidate_ids:
            return [], 0

        ordered_matches = [
            self._id_lookup[identifier].raw
            for identifier in self._ordered_ids
            if identifier in candidate_ids and identifier in self._id_lookup
        ]

        total = len(ordered_matches)
        if limit is None:
            limit = total
        start = max(offset, 0)
        end = start + limit if limit is not None else None
        paginated = ordered_matches[start:end]
        return paginated, total

    def add(self, question: Mapping[str, Any]) -> None:
        """Add a single *question* to the index."""

        record = QuestionRecord.from_mapping(question)
        identifier = record.raw.get("id")
        if not isinstance(identifier, str):
            self._records.append(record)
            return

        self._records.append(record)
        self._id_lookup[identifier] = record
        self._ordered_ids.append(identifier)
        for token in record.search_tokens:
            self._token_index.setdefault(token, set()).add(identifier)
        for tag in record.tags:
            self._tag_index.setdefault(tag, set()).add(identifier)
        for key, values in record.metadata_index.items():
            target = self._metadata_index.setdefault(key, {})
            for value in values:
                target.setdefault(value, set()).add(identifier)

        metadata = record.raw.get("metadata", {})
        if isinstance(metadata, Mapping):
            if isinstance(metadata.get("subject"), str):
                self._filter_values.setdefault("subjects", []).append(metadata["subject"])
            if isinstance(metadata.get("system"), str):
                self._filter_values.setdefault("systems", []).append(metadata["system"])
            if isinstance(metadata.get("status"), str):
                self._filter_values.setdefault("statuses", []).append(metadata["status"])
            if isinstance(metadata.get("difficulty"), str):
                self._filter_values.setdefault("difficulties", []).append(metadata["difficulty"])
        if isinstance(record.raw.get("tags"), Sequence):
            for tag in record.raw.get("tags", []):
                if isinstance(tag, str):
                    self._filter_values.setdefault("tags", []).append(tag)

        fingerprint = self._fingerprint()
        self._persist_index(fingerprint)

    def all(self) -> List[Mapping[str, Any]]:
        """Return all indexed question payloads."""

        return [record.raw for record in self._records]

    def filter_values(self) -> Dict[str, List[str]]:
        return {
            key: sorted(set(values)) for key, values in self._filter_values.items()
        }
