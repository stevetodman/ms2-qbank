import { resolveEnv } from '../utils/env.ts';

const ASSESSMENTS_API_BASE_URL = resolveEnv('VITE_ASSESSMENTS_API_BASE_URL', '/api/assessments');

export interface AssessmentBlueprint {
  candidateId: string;
  subject?: string | null;
  system?: string | null;
  difficulty?: string | null;
  tags: string[];
  timeLimitMinutes: number;
}

export interface AssessmentCreateResponse {
  assessmentId: string;
  questionCount: number;
  status: string;
}

export interface AssessmentChoice {
  label: string;
  text: string;
}

export interface AssessmentQuestion {
  id: string;
  stem: string;
  choices: AssessmentChoice[];
}

export interface AssessmentStartResponse {
  assessmentId: string;
  startedAt: string;
  expiresAt: string | null;
  timeLimitSeconds: number | null;
  questions: AssessmentQuestion[];
}

export interface AssessmentResponseItem {
  questionId: string;
  answer: string | null;
}

export interface AssessmentSubmitRequest {
  responses: AssessmentResponseItem[];
}

export interface AssessmentScoreBreakdown {
  totalQuestions: number;
  correct: number;
  incorrect: number;
  omitted: number;
  percentage: number;
  durationSeconds: number | null;
}

export interface AssessmentSubmissionResponse {
  assessmentId: string;
  submittedAt: string;
  score: AssessmentScoreBreakdown;
}

export interface AssessmentScoreResponse {
  assessmentId: string;
  completedAt: string;
  score: AssessmentScoreBreakdown;
}

function normaliseBlueprint(payload: AssessmentBlueprint) {
  return {
    candidate_id: payload.candidateId,
    subject: payload.subject ?? null,
    system: payload.system ?? null,
    difficulty: payload.difficulty ?? null,
    tags: payload.tags,
    time_limit_minutes: payload.timeLimitMinutes,
  };
}

function mapCreateResponse(json: { assessment_id: string; question_count: number; status: string }) {
  return {
    assessmentId: json.assessment_id,
    questionCount: json.question_count,
    status: json.status,
  } satisfies AssessmentCreateResponse;
}

function mapStartResponse(json: {
  assessment_id: string;
  started_at: string;
  expires_at: string | null;
  time_limit_seconds: number | null;
  questions: { id: string; stem: string; choices: { label: string; text: string }[] }[];
}) {
  return {
    assessmentId: json.assessment_id,
    startedAt: json.started_at,
    expiresAt: json.expires_at,
    timeLimitSeconds: json.time_limit_seconds,
    questions: json.questions,
  } satisfies AssessmentStartResponse;
}

function mapScoreBreakdown(json: {
  total_questions: number;
  correct: number;
  incorrect: number;
  omitted: number;
  percentage: number;
  duration_seconds: number | null;
}): AssessmentScoreBreakdown {
  return {
    totalQuestions: json.total_questions,
    correct: json.correct,
    incorrect: json.incorrect,
    omitted: json.omitted,
    percentage: json.percentage,
    durationSeconds: json.duration_seconds,
  };
}

function mapSubmissionResponse(json: {
  assessment_id: string;
  submitted_at: string;
  score: {
    total_questions: number;
    correct: number;
    incorrect: number;
    omitted: number;
    percentage: number;
    duration_seconds: number | null;
  };
}): AssessmentSubmissionResponse {
  return {
    assessmentId: json.assessment_id,
    submittedAt: json.submitted_at,
    score: mapScoreBreakdown(json.score),
  };
}

function mapScoreResponse(json: {
  assessment_id: string;
  completed_at: string;
  score: {
    total_questions: number;
    correct: number;
    incorrect: number;
    omitted: number;
    percentage: number;
    duration_seconds: number | null;
  };
}): AssessmentScoreResponse {
  return {
    assessmentId: json.assessment_id,
    completedAt: json.completed_at,
    score: mapScoreBreakdown(json.score),
  };
}

export async function createAssessment(payload: AssessmentBlueprint): Promise<AssessmentCreateResponse> {
  const response = await fetch(`${ASSESSMENTS_API_BASE_URL}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(normaliseBlueprint(payload)),
  });
  if (!response.ok) {
    throw new Error(`Failed to create assessment (status ${response.status})`);
  }
  const json = (await response.json()) as {
    assessment_id: string;
    question_count: number;
    status: string;
  };
  return mapCreateResponse(json);
}

export async function startAssessment(assessmentId: string): Promise<AssessmentStartResponse> {
  const response = await fetch(`${ASSESSMENTS_API_BASE_URL}/${assessmentId}/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to start assessment (status ${response.status})`);
  }
  const json = (await response.json()) as {
    assessment_id: string;
    started_at: string;
    expires_at: string | null;
    time_limit_seconds: number | null;
    questions: { id: string; stem: string; choices: { label: string; text: string }[] }[];
  };
  return mapStartResponse(json);
}

export async function submitAssessment(
  assessmentId: string,
  payload: AssessmentSubmitRequest
): Promise<AssessmentSubmissionResponse> {
  const response = await fetch(`${ASSESSMENTS_API_BASE_URL}/${assessmentId}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      responses: payload.responses.map((item) => ({
        question_id: item.questionId,
        answer: item.answer,
      })),
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to submit assessment (status ${response.status})`);
  }
  const json = (await response.json()) as {
    assessment_id: string;
    submitted_at: string;
    score: {
      total_questions: number;
      correct: number;
      incorrect: number;
      omitted: number;
      percentage: number;
      duration_seconds: number | null;
    };
  };
  return mapSubmissionResponse(json);
}

export async function fetchAssessmentScore(assessmentId: string): Promise<AssessmentScoreResponse> {
  const response = await fetch(`${ASSESSMENTS_API_BASE_URL}/${assessmentId}/score`);
  if (!response.ok) {
    throw new Error(`Failed to load assessment score (status ${response.status})`);
  }
  const json = (await response.json()) as {
    assessment_id: string;
    completed_at: string;
    score: {
      total_questions: number;
      correct: number;
      incorrect: number;
      omitted: number;
      percentage: number;
      duration_seconds: number | null;
    };
  };
  return mapScoreResponse(json);
}
