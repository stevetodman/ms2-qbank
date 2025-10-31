from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import List

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

@pytest.fixture
def sample_questions() -> List[dict]:
    data_path = PROJECT_ROOT / "data" / "questions" / "sample_questions.json"
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
