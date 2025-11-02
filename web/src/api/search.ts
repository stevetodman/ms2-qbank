import type { PracticeFilters, QuestionPayload } from '../types/practice';
import { resolveEnv } from '../utils/env';

const SEARCH_API_BASE_URL = resolveEnv('VITE_SEARCH_API_BASE_URL', '/api/search');

export interface SearchResponse {
  data: QuestionPayload[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    returned: number;
  };
}

export interface SearchPayload {
  query?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  limit: number;
  offset?: number;
}

export interface FilterResponse {
  subjects: string[];
  systems: string[];
  statuses: string[];
  difficulties: string[];
  tags: string[];
}

export async function fetchSearchFilters(): Promise<FilterResponse> {
  const response = await fetch(`${SEARCH_API_BASE_URL}/filters`);
  if (!response.ok) {
    throw new Error(`Failed to load filters (status ${response.status})`);
  }
  return (await response.json()) as FilterResponse;
}

export async function requestSearch(payload: SearchPayload): Promise<SearchResponse> {
  const response = await fetch(`${SEARCH_API_BASE_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Search request failed with status ${response.status}`);
  }

  const json = (await response.json()) as SearchResponse;
  return json;
}

export async function buildSearchPayload(
  filters: PracticeFilters,
  overrides: Partial<Pick<SearchPayload, 'limit' | 'offset'>> = {}
): Promise<SearchPayload> {
  const metadata: Record<string, unknown> = {};
  if (filters.subject) {
    metadata.subject = filters.subject;
  }
  if (filters.system) {
    metadata.system = filters.system;
  }
  if (filters.status) {
    metadata.status = filters.status;
  }
  if (filters.difficulty) {
    metadata.difficulty = filters.difficulty;
  }

  return {
    query: filters.query?.trim() || undefined,
    tags: filters.tags.length > 0 ? filters.tags : undefined,
    metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
    limit: overrides.limit ?? filters.questionCount,
    offset: overrides.offset ?? 0,
  };
}

export async function searchQuestions(
  filters: PracticeFilters,
  overrides: Partial<Pick<SearchPayload, 'limit' | 'offset'>> = {}
): Promise<SearchResponse> {
  const payload = await buildSearchPayload(filters, overrides);
  return requestSearch(payload);
}
