from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest


@pytest.fixture
def sample_questions() -> List[dict]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "questions" / "sample_questions.json"
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
