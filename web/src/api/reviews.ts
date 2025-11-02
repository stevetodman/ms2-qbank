import type { PracticeMode } from '../types/practice';
import { resolveEnv } from '../utils/env';

const REVIEW_API_BASE_URL = resolveEnv('VITE_REVIEW_API_BASE_URL', '/api/reviews');

export interface ReviewEventPayload {
  reviewer: string;
  action: 'approve' | 'reject' | 'comment';
  role: 'author' | 'reviewer' | 'editor' | 'admin';
  comment?: string;
}

export interface ReviewEventResponse {
  reviewer: string;
  action: 'approve' | 'reject' | 'comment';
  timestamp: string;
  role: string;
  comment?: string | null;
}

export interface ReviewSummary {
  question_id: string;
  current_status: string;
  history: ReviewEventResponse[];
  allowed_actions: string[];
}

async function requestReview(
  questionId: string,
  init?: RequestInit
): Promise<ReviewSummary> {
  const response = await fetch(`${REVIEW_API_BASE_URL}/questions/${questionId}/reviews`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...init,
  });

  if (!response.ok) {
    let message = `Review request failed with status ${response.status}`;
    try {
      const errorBody = (await response.json()) as { detail?: unknown };
      if (typeof errorBody?.detail === 'string') {
        message = errorBody.detail;
      } else if (Array.isArray(errorBody?.detail) && errorBody.detail.length > 0) {
        const first = errorBody.detail[0];
        if (typeof first?.msg === 'string') {
          message = first.msg;
        }
      }
    } catch (err) {
      /* ignore JSON parsing errors */
    }
    throw new Error(message);
  }

  return (await response.json()) as ReviewSummary;
}

export function getReviewSummary(questionId: string): Promise<ReviewSummary> {
  return requestReview(questionId, { method: 'GET' });
}

export function submitReviewAction(
  questionId: string,
  payload: ReviewEventPayload
): Promise<ReviewSummary> {
  return requestReview(questionId, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function bookmarkQuestion(questionId: string, reviewer: string) {
  return submitReviewAction(questionId, {
    reviewer,
    action: 'comment',
    role: 'reviewer',
    comment: '#bookmark',
  });
}

export function tagQuestion(questionId: string, reviewer: string, tag: string) {
  return submitReviewAction(questionId, {
    reviewer,
    action: 'comment',
    role: 'reviewer',
    comment: `#tag:${tag}`,
  });
}

export function escalateForReview(
  questionId: string,
  reviewer: string,
  mode: PracticeMode,
  comment?: string
) {
  const payload: ReviewEventPayload = {
    reviewer,
    role: mode === 'tutor' ? 'author' : 'reviewer',
    action: 'comment',
    comment: comment ?? 'Requires editorial follow-up',
  };
  return submitReviewAction(questionId, payload);
}
