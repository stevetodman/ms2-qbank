"""FastAPI service for database-backed self-assessments."""

import json
import itertools
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db_store import AssessmentDatabaseStore
from .db_models import (
    AssessmentBlueprintCreate,
    AssessmentResponse,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentSubmissionResponse,
    AssessmentScoreResponse,
    AssessmentQuestionResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="MS2 QBank Self-Assessment API",
    description="Database-backed self-assessment service",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize store
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "assessments.db"
QUESTIONS_DIR = DATA_DIR / "questions"

store = AssessmentDatabaseStore(db_path=str(DB_PATH), question_count=160)


def load_questions() -> list[dict]:
    """Load all questions from the data directory."""
    questions = []
    if not QUESTIONS_DIR.exists():
        return questions

    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse question dataset: {path}") from exc

        if isinstance(payload, list):
            questions.extend([item for item in payload if isinstance(item, dict)])
        elif isinstance(payload, dict):
            questions.append(payload)

    return questions


def filter_questions(
    questions: list[dict],
    subject: Optional[str] = None,
    system: Optional[str] = None,
    difficulty: Optional[str] = None,
    tags: list[str] = None,
) -> list[dict]:
    """Filter questions based on criteria."""
    filtered = []

    for question in questions:
        metadata = question.get("metadata", {})
        q_tags = question.get("tags", [])

        # Apply filters
        if subject and metadata.get("subject") != subject:
            continue
        if system and metadata.get("system") != system:
            continue
        if difficulty and metadata.get("difficulty") != difficulty:
            continue
        if tags:
            q_tag_set = set(q_tags)
            if not set(tags).issubset(q_tag_set):
                continue

        filtered.append(question)

    return filtered


def select_questions(
    questions: list[dict], count: int = 160
) -> list[dict]:
    """Select questions for the assessment (cycling if needed)."""
    if not questions:
        raise ValueError("No questions match the requested filters")

    selected = []
    iterator = itertools.cycle(questions)

    for i in range(count):
        original = dict(next(iterator))
        source_id = original.get("id")

        # Create delivery ID
        if isinstance(source_id, str):
            delivery_id = f"{source_id}__{i + 1}"
        else:
            delivery_id = f"question__{i + 1}"

        original.setdefault("_source_id", source_id)
        original["id"] = delivery_id
        selected.append(original)

    return selected


@app.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(blueprint: AssessmentBlueprintCreate) -> AssessmentResponse:
    """Create a new assessment."""
    try:
        assessment = store.create(
            candidate_id=blueprint.candidate_id,
            subject=blueprint.subject,
            system=blueprint.system,
            difficulty=blueprint.difficulty,
            tags=blueprint.tags,
            time_limit_minutes=blueprint.time_limit_minutes,
        )

        return AssessmentResponse(
            assessment_id=assessment.assessment_id,
            candidate_id=assessment.candidate_id,
            status=assessment.status,
            question_count=store.question_count,
            time_limit_minutes=assessment.time_limit_minutes,
            created_at=assessment.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assessments/{assessment_id}/start", response_model=AssessmentStartResponse)
async def start_assessment(assessment_id: str) -> AssessmentStartResponse:
    """Start an assessment and deliver questions."""
    try:
        # Get the assessment
        assessment = store.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Load and filter questions
        all_questions = load_questions()
        import json as json_lib
        tags = json_lib.loads(assessment.tags) if assessment.tags else []

        filtered = filter_questions(
            all_questions,
            subject=assessment.subject,
            system=assessment.system,
            difficulty=assessment.difficulty,
            tags=tags,
        )

        # Select questions for the assessment
        selected = select_questions(filtered, count=store.question_count)
        question_ids = [q["id"] for q in selected]

        # Start the assessment
        started = store.start(assessment_id, question_ids)

        # Prepare question responses
        questions = []
        for q in selected:
            choices = q.get("choices", [])
            questions.append(
                AssessmentQuestionResponse(
                    id=q["id"],
                    stem=q.get("stem", ""),
                    choices=choices,
                )
            )

        # Calculate time limit in seconds
        time_limit_seconds = (
            started.time_limit_minutes * 60 if started.time_limit_minutes > 0 else None
        )

        return AssessmentStartResponse(
            assessment_id=started.assessment_id,
            started_at=started.started_at,
            expires_at=started.expires_at,
            time_limit_seconds=time_limit_seconds,
            questions=questions,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assessments/{assessment_id}/submit", response_model=AssessmentSubmissionResponse)
async def submit_assessment(
    assessment_id: str, submission: AssessmentSubmitRequest
) -> AssessmentSubmissionResponse:
    """Submit assessment responses and get score."""
    try:
        # Get the assessment
        assessment = store.get(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Load questions to get correct answers
        all_questions = load_questions()
        question_map = {q["id"]: q for q in all_questions}

        # Build responses and correct answers maps
        responses = {}
        correct_answers = {}

        import json as json_lib
        question_ids = json_lib.loads(assessment.question_ids)

        for item in submission.responses:
            qid = item.get("question_id")
            answer = item.get("answer")

            if qid in question_ids:
                responses[qid] = answer

                # Get correct answer (strip delivery suffix)
                source_id = qid.split("__")[0] if "__" in qid else qid
                if source_id in question_map:
                    correct_answers[qid] = question_map[source_id].get("answer")

        # Submit to store
        submitted = store.submit(assessment_id, responses, correct_answers)

        # Build response
        score = AssessmentScoreResponse(
            total_questions=submitted.total_questions,
            correct=submitted.correct,
            incorrect=submitted.incorrect,
            omitted=submitted.omitted,
            percentage=submitted.percentage,
            duration_seconds=submitted.duration_seconds,
        )

        return AssessmentSubmissionResponse(
            assessment_id=submitted.assessment_id,
            submitted_at=submitted.submitted_at,
            score=score,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessments/{assessment_id}/score", response_model=AssessmentScoreResponse)
async def get_assessment_score(assessment_id: str) -> AssessmentScoreResponse:
    """Get score for a completed assessment."""
    try:
        score = store.get_score(assessment_id)
        if not score:
            raise HTTPException(status_code=404, detail="Assessment not found or not completed")

        return score

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "self-assessment-db"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)
