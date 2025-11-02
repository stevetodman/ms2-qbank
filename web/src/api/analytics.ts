import { resolveEnv } from '../utils/env';

const ANALYTICS_API_BASE_URL = resolveEnv('VITE_ANALYTICS_API_BASE_URL', '/api/analytics');

interface RawUsageDistributionBucket {
  deliveries?: number;
  questions?: number;
}

interface RawAnalyticsUsageSummary {
  tracked_questions?: number;
  total_usage?: number;
  average_usage?: number;
  minimum_usage?: number;
  maximum_usage?: number;
  usage_distribution?: RawUsageDistributionBucket[];
}

interface RawAnalyticsMetrics {
  total_questions?: number;
  difficulty_distribution?: Record<string, number>;
  review_status_distribution?: Record<string, number>;
  usage_summary?: RawAnalyticsUsageSummary;
}

interface RawAnalyticsArtifact {
  json_path?: string;
  markdown_path?: string;
}

interface RawAnalyticsResponse {
  generated_at?: string;
  metrics?: RawAnalyticsMetrics;
  artifact?: RawAnalyticsArtifact;
  is_fresh?: boolean;
}

export interface AnalyticsUsageBucket {
  deliveries: number;
  questions: number;
}

export interface AnalyticsUsageSummary {
  trackedQuestions: number;
  totalUsage: number;
  averageUsage: number;
  minimumUsage: number;
  maximumUsage: number;
  usageDistribution: AnalyticsUsageBucket[];
}

export interface AnalyticsMetrics {
  totalQuestions: number;
  difficultyDistribution: Record<string, number>;
  reviewStatusDistribution: Record<string, number>;
  usageSummary: AnalyticsUsageSummary;
}

export interface AnalyticsArtifact {
  jsonPath: string;
  markdownPath: string;
}

export interface AnalyticsSnapshot {
  generatedAt: string;
  metrics: AnalyticsMetrics;
  artifact: AnalyticsArtifact;
  isFresh: boolean;
}

function normaliseUsageDistribution(
  buckets: RawAnalyticsUsageSummary['usage_distribution']
): AnalyticsUsageBucket[] {
  if (!Array.isArray(buckets)) {
    return [];
  }

  return buckets
    .filter((bucket): bucket is RawUsageDistributionBucket => bucket !== null && typeof bucket === 'object')
    .map((bucket) => ({
      deliveries: typeof bucket.deliveries === 'number' ? bucket.deliveries : 0,
      questions: typeof bucket.questions === 'number' ? bucket.questions : 0,
    }))
    .sort((a, b) => a.deliveries - b.deliveries);
}

function normaliseUsageSummary(raw: RawAnalyticsUsageSummary | undefined): AnalyticsUsageSummary {
  return {
    trackedQuestions: typeof raw?.tracked_questions === 'number' ? raw.tracked_questions : 0,
    totalUsage: typeof raw?.total_usage === 'number' ? raw.total_usage : 0,
    averageUsage: typeof raw?.average_usage === 'number' ? raw.average_usage : 0,
    minimumUsage: typeof raw?.minimum_usage === 'number' ? raw.minimum_usage : 0,
    maximumUsage: typeof raw?.maximum_usage === 'number' ? raw.maximum_usage : 0,
    usageDistribution: normaliseUsageDistribution(raw?.usage_distribution),
  };
}

function normaliseMetrics(raw: RawAnalyticsMetrics | undefined): AnalyticsMetrics {
  return {
    totalQuestions: typeof raw?.total_questions === 'number' ? raw.total_questions : 0,
    difficultyDistribution: raw?.difficulty_distribution ?? {},
    reviewStatusDistribution: raw?.review_status_distribution ?? {},
    usageSummary: normaliseUsageSummary(raw?.usage_summary),
  };
}

function normaliseArtifact(raw: RawAnalyticsArtifact | undefined): AnalyticsArtifact {
  return {
    jsonPath: typeof raw?.json_path === 'string' ? raw.json_path : '',
    markdownPath: typeof raw?.markdown_path === 'string' ? raw.markdown_path : '',
  };
}

function normaliseResponse(raw: RawAnalyticsResponse): AnalyticsSnapshot {
  return {
    generatedAt: typeof raw.generated_at === 'string' ? raw.generated_at : '',
    metrics: normaliseMetrics(raw.metrics),
    artifact: normaliseArtifact(raw.artifact),
    isFresh: Boolean(raw.is_fresh),
  };
}

export async function fetchLatestAnalytics(): Promise<AnalyticsSnapshot> {
  const response = await fetch(`${ANALYTICS_API_BASE_URL}/analytics/latest`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Analytics request failed with status ${response.status}`);
  }

  const json = (await response.json()) as RawAnalyticsResponse;
  return normaliseResponse(json);
}

export type { AnalyticsSnapshot as AnalyticsResponse };
