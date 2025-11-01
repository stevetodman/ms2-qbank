import { apiClient } from './client';

// Types matching backend models
export interface SubjectPerformance {
  subject: string;
  total_attempts: number;
  correct: number;
  incorrect: number;
  accuracy_percent: number;
  average_time_seconds: number;
}

export interface SystemPerformance {
  system: string;
  total_attempts: number;
  correct: number;
  incorrect: number;
  accuracy_percent: number;
  average_time_seconds: number;
}

export interface DifficultyPerformance {
  difficulty: string;
  total_attempts: number;
  correct: number;
  incorrect: number;
  accuracy_percent: number;
}

export interface DailyPerformance {
  date: string;
  total_attempts: number;
  correct: number;
  incorrect: number;
  accuracy_percent: number;
  study_time_seconds: number;
}

export interface WeakArea {
  category: string;
  name: string;
  total_attempts: number;
  accuracy_percent: number;
  rank: number;
}

export interface UserAnalytics {
  user_id: number;
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  omitted_attempts: number;
  accuracy_percent: number;
  average_time_seconds: number;
  total_study_time_hours: number;
  questions_attempted_count: number;
  assessments_completed: number;
  current_streak_days: number;
  by_subject: SubjectPerformance[];
  by_system: SystemPerformance[];
  by_difficulty: DifficultyPerformance[];
  daily_performance: DailyPerformance[];
  weak_areas: WeakArea[];
  strongest_subject: string | null;
  weakest_subject: string | null;
  first_attempt_at: string | null;
  last_attempt_at: string | null;
}

export interface PercentileRanking {
  user_id: number;
  overall_percentile: number;
  accuracy_percentile: number;
  speed_percentile: number;
  volume_percentile: number;
  total_users: number;
}

export interface AttemptCreate {
  question_id: string;
  assessment_id?: string;
  subject?: string;
  system?: string;
  difficulty?: string;
  answer_given?: string;
  correct_answer: string;
  is_correct: boolean;
  time_seconds?: number;
  mode?: string;
  marked?: boolean;
  omitted?: boolean;
}

const ANALYTICS_BASE = 'http://localhost:8008';

// Record a question attempt
export async function recordAttempt(data: AttemptCreate, token?: string): Promise<{ success: boolean; attempt_id: number }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  return apiClient(`${ANALYTICS_BASE}/attempts`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
}

// Get user analytics
export async function getUserAnalytics(days: number = 30, token: string): Promise<UserAnalytics> {
  return apiClient(`${ANALYTICS_BASE}/analytics?days=${days}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// Get percentile ranking
export async function getPercentileRanking(token: string): Promise<PercentileRanking> {
  return apiClient(`${ANALYTICS_BASE}/analytics/percentile`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

// Utility functions
export function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

export function formatHours(hours: number): string {
  if (hours < 1) {
    return `${Math.round(hours * 60)}m`;
  }
  return `${hours.toFixed(1)}h`;
}

export function getAccuracyColor(accuracy: number): string {
  if (accuracy >= 80) return '#10b981'; // green
  if (accuracy >= 70) return '#f59e0b'; // yellow
  return '#ef4444'; // red
}

export function getPercentileLabel(percentile: number): string {
  if (percentile >= 90) return 'Excellent';
  if (percentile >= 75) return 'Good';
  if (percentile >= 50) return 'Average';
  if (percentile >= 25) return 'Below Average';
  return 'Needs Improvement';
}
