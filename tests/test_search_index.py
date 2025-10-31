from __future__ import annotations

from search import QuestionIndex


def build_index(sample_questions):
    return QuestionIndex(sample_questions)


def test_keyword_search_includes_metadata_keywords(sample_questions):
    index = build_index(sample_questions)
    results = index.search(query="deep vein thrombosis")
    assert [question["id"] for question in results] == ["q_1a2b3c4d"]


def test_tag_filters_and_keyword_search_work_together(sample_questions):
    index = build_index(sample_questions)
    results = index.search(query="streptococcal", tags={"infection"})
    assert [question["id"] for question in results] == ["q_5e6f7a8b"]


def test_tag_filters_and_keyword_search_require_both(sample_questions):
    index = build_index(sample_questions)
    results = index.search(query="streptococcal", tags={"vascular"})
    assert results == []


def test_metadata_filters_select_by_subject(sample_questions):
    index = build_index(sample_questions)
    results = index.search(metadata_filters={"subject": "microbiology"})
    assert [question["id"] for question in results] == ["q_5e6f7a8b"]


def test_metadata_filter_with_multiple_allowed_values(sample_questions):
    index = build_index(sample_questions)
    results = index.search(metadata_filters={"difficulty": ["medium", "hard"]})
    assert [question["id"] for question in results] == ["q_1a2b3c4d"]


def test_reference_metadata_contributes_to_keyword_search(sample_questions):
    index = build_index(sample_questions)
    results = index.search(query="clinical features")
    assert [question["id"] for question in results] == ["q_1a2b3c4d"]
