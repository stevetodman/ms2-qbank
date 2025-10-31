from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest


@pytest.fixture
def sample_questions() -> List[dict]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "questions" / "sample_questions.json"
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
