from __future__ import annotations

from analytics import compute_question_metrics


def test_compute_question_metrics(sample_questions):
    metrics = compute_question_metrics(sample_questions)

    assert metrics.total_questions == len(sample_questions)
    assert metrics.difficulty_distribution == {"Easy": 1, "Medium": 1}
    assert metrics.review_status_distribution == {"Unused": 2}

    usage = metrics.usage_summary
    assert usage.tracked_questions == 2
    assert usage.total_usage == 25
    assert usage.minimum_usage == 7
    assert usage.maximum_usage == 18
    assert usage.usage_distribution == {7: 1, 18: 1}
    assert usage.average_usage == 12.5


def test_compute_question_metrics_handles_missing_metadata():
    sample = [
        {"metadata": {"difficulty": "Hard", "status": "Correct", "usage_count": "9"}},
        {"metadata": {"difficulty": "Medium", "status": "Incorrect", "usage_count": 0}},
        {"metadata": {"difficulty": "Medium", "status": "Correct"}},
        {},
    ]

    metrics = compute_question_metrics(sample)

    assert metrics.total_questions == len(sample)
    assert metrics.difficulty_distribution == {"Hard": 1, "Medium": 2}
    assert metrics.review_status_distribution == {"Correct": 2, "Incorrect": 1}

    usage = metrics.usage_summary
    assert usage.tracked_questions == 2
    assert usage.total_usage == 9
    assert usage.minimum_usage == 0
    assert usage.maximum_usage == 9
    assert usage.usage_distribution == {0: 1, 9: 1}
    assert usage.average_usage == 4.5
