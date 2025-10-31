export type PracticeMode = 'timed' | 'tutor' | 'custom';

export interface QuestionChoice {
  label: string;
  text: string;
}

export interface QuestionExplanation {
  summary: string;
  rationales?: Array<{ choice: string; text: string }>;
}

export interface QuestionMetadata {
  subject?: string;
  system?: string;
  difficulty?: string;
  status?: string;
  [key: string]: unknown;
}

export interface QuestionPayload {
  id: string;
  stem: string;
  choices: QuestionChoice[];
  answer: string;
  explanation?: QuestionExplanation;
  metadata?: QuestionMetadata;
  tags?: string[];
}

export interface PracticeFilters {
  query?: string;
  tags: string[];
  subject?: string;
  system?: string;
  status?: string;
  difficulty?: string;
  questionCount: number;
  randomizeOrder: boolean;
  timePerQuestionSeconds?: number;
  showExplanationOnSubmit?: boolean;
}

export interface QuestionPerformance {
  questionId: string;
  questionIndex: number;
  selectedAnswer?: string;
  correctAnswer: string;
  correct: boolean;
  timeSeconds: number;
}

export interface PracticeSummary {
  mode: PracticeMode;
  filters: PracticeFilters;
  totalQuestions: number;
  correctCount: number;
  incorrectCount: number;
  omittedCount: number;
  averageTimeSeconds: number;
  questionPerformances: QuestionPerformance[];
  completedAt: number;
}

export interface PracticeSession {
  mode: PracticeMode;
  filters: PracticeFilters;
  questions: QuestionPayload[];
  answers: Record<string, string | undefined>;
  reveals: Record<string, boolean>;
  currentIndex: number;
  startedAt: number;
  totalDurationSeconds: number | null;
  remainingSeconds: number | null;
  completed: boolean;
  questionDurationsMs: Record<string, number>;
  questionStartedAt: number | null;
  summary: PracticeSummary | null;
}

export const LAST_SUMMARY_STORAGE_KEY = 'ms2:lastSummary';
