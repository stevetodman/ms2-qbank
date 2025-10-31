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
}
