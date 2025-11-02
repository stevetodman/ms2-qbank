import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  fetchSearchFilters,
  searchQuestions,
} from '../api/search';
import type {
  PracticeFilters,
  PracticeMode,
  PracticeSession,
  PracticeSummary,
  QuestionPayload,
} from '../types/practice';
import { LAST_SUMMARY_STORAGE_KEY } from '../types/practice';
import { shuffle } from '../utils/shuffle';
import { useAuth } from './AuthContext';
import * as analyticsApi from '../api/userAnalytics';

interface FilterOptions {
  subjects: string[];
  systems: string[];
  statuses: string[];
  difficulties: string[];
  tags: string[];
}

interface PracticeSessionContextValue {
  session: PracticeSession | null;
  isLoading: boolean;
  error: string | null;
  filterOptions: FilterOptions;
  filtersLoading: boolean;
  preview: QuestionPayload[];
  previewTotal: number;
  previewError: string | null;
  previewLoading: boolean;
  canLoadMorePreview: boolean;
  loadPreview: (filters: PracticeFilters, append?: boolean) => Promise<void>;
  loadMorePreview: () => Promise<void>;
  startSession: (mode: PracticeMode, filters: PracticeFilters) => Promise<void>;
  selectAnswer: (questionId: string, choice: string) => void;
  goToQuestion: (index: number) => void;
  revealExplanation: (questionId: string) => void;
  completeSession: () => void;
  resetSession: () => void;
}

const PracticeSessionContext = createContext<PracticeSessionContextValue | undefined>(
  undefined
);

const defaultFilterOptions: FilterOptions = {
  subjects: [],
  systems: [],
  statuses: [],
  difficulties: [],
  tags: [],
};

const PREVIEW_PAGE_SIZE = 10;

function cloneFilters(filters: PracticeFilters): PracticeFilters {
  return {
    ...filters,
    tags: [...filters.tags],
  };
}

function initialiseReveals(mode: PracticeMode, filters: PracticeFilters, questions: QuestionPayload[]) {
  const reveals: Record<string, boolean> = {};
  const autoReveal = mode === 'tutor' || (mode === 'custom' && filters.showExplanationOnSubmit);
  questions.forEach((question) => {
    reveals[question.id] = autoReveal ? false : false;
  });
  return reveals;
}

function deriveTotalDuration(
  mode: PracticeMode,
  filters: PracticeFilters,
  questionCount: number
): number | null {
  const fallbackSeconds = filters.timePerQuestionSeconds ?? 105;
  if (mode === 'timed') {
    return questionCount * fallbackSeconds;
  }
  if (mode === 'custom' && filters.timePerQuestionSeconds) {
    return questionCount * filters.timePerQuestionSeconds;
  }
  return null;
}

function toSeconds(milliseconds: number): number {
  return Math.max(0, Math.round(milliseconds / 1000));
}

function accumulateCurrentQuestionDuration(session: PracticeSession, now: number) {
  const durations = { ...session.questionDurationsMs };
  if (session.questionStartedAt === null) {
    return { durations, questionStartedAt: session.questionStartedAt };
  }
  const activeQuestion = session.questions[session.currentIndex];
  if (!activeQuestion) {
    return { durations, questionStartedAt: session.questionStartedAt };
  }
  const elapsed = Math.max(0, now - session.questionStartedAt);
  durations[activeQuestion.id] = (durations[activeQuestion.id] ?? 0) + elapsed;
  return { durations, questionStartedAt: now };
}

function computeSummary(
  session: PracticeSession,
  durations: Record<string, number>,
  completedAt: number
): PracticeSummary {
  const questionPerformances = session.questions.map((question, index) => {
    const selectedAnswer = session.answers[question.id];
    const durationMs = durations[question.id] ?? 0;
    return {
      questionId: question.id,
      questionIndex: index,
      selectedAnswer,
      correctAnswer: question.answer,
      correct: selectedAnswer === question.answer,
      timeSeconds: toSeconds(durationMs),
    };
  });

  const totalQuestions = questionPerformances.length;
  const correctCount = questionPerformances.filter((performance) => performance.correct).length;
  const answeredCount = questionPerformances.filter((performance) => performance.selectedAnswer).length;
  const incorrectCount = answeredCount - correctCount;
  const omittedCount = totalQuestions - answeredCount;
  const totalTimeSeconds = questionPerformances.reduce(
    (total, performance) => total + performance.timeSeconds,
    0
  );
  const averageTimeSeconds =
    totalQuestions === 0 ? 0 : Math.round(totalTimeSeconds / totalQuestions);

  return {
    mode: session.mode,
    filters: session.filters,
    totalQuestions,
    correctCount,
    incorrectCount,
    omittedCount,
    averageTimeSeconds,
    questionPerformances,
    completedAt,
  };
}

function persistSummary(summary: PracticeSummary) {
  try {
    window.localStorage?.setItem(LAST_SUMMARY_STORAGE_KEY, JSON.stringify(summary));
  } catch (err) {
    console.warn('Unable to persist practice summary', err);
  }
}

async function recordAnalytics(
  summary: PracticeSummary,
  questions: QuestionPayload[],
  token?: string
) {
  if (!token) {
    return; // Skip analytics if user not logged in
  }

  try {
    // Record each question attempt
    const recordPromises = summary.questionPerformances.map((perf) => {
      const question = questions.find((q) => q.id === perf.questionId);
      if (!question) return Promise.resolve();

      return analyticsApi.recordAttempt(
        {
          question_id: perf.questionId,
          answer_given: perf.selectedAnswer || undefined,
          correct_answer: perf.correctAnswer,
          is_correct: perf.correct,
          time_seconds: perf.timeSeconds,
          subject: question.metadata?.subject,
          system: question.metadata?.system,
          difficulty: question.metadata?.difficulty,
          mode: summary.mode === 'tutor' ? 'tutor' : summary.mode === 'timed' ? 'assessment' : 'practice',
          omitted: !perf.selectedAnswer,
        },
        token
      );
    });

    await Promise.all(recordPromises);
  } catch (err) {
    console.warn('Failed to record analytics', err);
  }
}

function finaliseSession(session: PracticeSession, now: number): PracticeSession {
  if (session.summary) {
    return {
      ...session,
      completed: true,
      remainingSeconds: 0,
      questionStartedAt: null,
    };
  }

  const { durations } = accumulateCurrentQuestionDuration(session, now);
  const summary = computeSummary(session, durations, now);
  persistSummary(summary);

  const reveals = { ...session.reveals };
  session.questions.forEach((question) => {
    reveals[question.id] = true;
  });

  return {
    ...session,
    completed: true,
    remainingSeconds: 0,
    questionDurationsMs: durations,
    questionStartedAt: null,
    summary,
    reveals,
  };
}

export const PracticeSessionProvider = ({ children }: { children: ReactNode }) => {
  const { token } = useAuth();
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>(defaultFilterOptions);
  const [filtersLoading, setFiltersLoading] = useState(false);
  const [preview, setPreview] = useState<QuestionPayload[]>([]);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewCursor, setPreviewCursor] = useState(0);
  const previewFiltersRef = useRef<PracticeFilters | null>(null);

  const canLoadMorePreview = useMemo(() => previewCursor < previewTotal, [previewCursor, previewTotal]);

  useEffect(() => {
    let isActive = true;
    async function loadFilters() {
      setFiltersLoading(true);
      try {
        const filters = await fetchSearchFilters();
        if (!isActive) {
          return;
        }
        setFilterOptions(filters);
      } catch (err) {
        console.error('Failed to preload filter metadata', err);
        if (isActive) {
          setFilterOptions(defaultFilterOptions);
        }
      } finally {
        if (isActive) {
          setFiltersLoading(false);
        }
      }
    }
    void loadFilters();
    return () => {
      isActive = false;
    };
  }, []);

  const loadPreview = useCallback(
    async (filters: PracticeFilters, append = false) => {
      const baseFilters = append && previewFiltersRef.current ? previewFiltersRef.current : cloneFilters(filters);
      if (!append || !previewFiltersRef.current) {
        previewFiltersRef.current = cloneFilters(baseFilters);
      }
      if (!append) {
        setPreview([]);
        setPreviewTotal(0);
        setPreviewCursor(0);
      }
      setPreviewLoading(true);
      setPreviewError(null);
      try {
        const offset = append ? previewCursor : 0;
        const response = await searchQuestions(baseFilters, {
          limit: PREVIEW_PAGE_SIZE,
          offset,
        });
        const { data, pagination } = response;
        setPreview((current) => (append ? [...current, ...data] : data));
        setPreviewTotal(pagination.total);
        setPreviewCursor(pagination.offset + pagination.returned);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to preview questions';
        setPreviewError(message);
        if (!append) {
          setPreview([]);
          setPreviewTotal(0);
          setPreviewCursor(0);
        }
      } finally {
        setPreviewLoading(false);
      }
    },
    [previewCursor]
  );

  const loadMorePreview = useCallback(async () => {
    const stored = previewFiltersRef.current;
    if (!stored) {
      return;
    }
    await loadPreview(stored, true);
  }, [loadPreview]);

  useEffect(() => {
    if (!session || session.totalDurationSeconds === null || session.completed) {
      return;
    }
    const interval = window.setInterval(() => {
      setSession((current) => {
        if (!current || current.totalDurationSeconds === null || current.completed) {
          return current;
        }
        const base = current.remainingSeconds ?? current.totalDurationSeconds;
        const nextValue = Math.max(base - 1, 0);
        if (nextValue === 0) {
          return finaliseSession(current, Date.now());
        }
        return {
          ...current,
          remainingSeconds: nextValue,
        };
      });
    }, 1000);
    return () => window.clearInterval(interval);
  }, [session]);

  const startSession = useCallback(
    async (mode: PracticeMode, filters: PracticeFilters) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await searchQuestions(filters, { limit: filters.questionCount, offset: 0 });
        const { data, pagination } = response;
        if (pagination.total === 0) {
          throw new Error('No questions match the selected filters.');
        }
        if (data.length < filters.questionCount) {
          throw new Error(
            `Only ${pagination.total} question${pagination.total === 1 ? '' : 's'} match the selected filters.`
          );
        }
        const ordered = filters.randomizeOrder ? shuffle(data) : data;
        const reveals = initialiseReveals(mode, filters, ordered);
        const totalDuration = deriveTotalDuration(mode, filters, ordered.length);
        const startedAt = Date.now();
        setSession({
          mode,
          filters,
          questions: ordered,
          answers: {},
          reveals,
          currentIndex: 0,
          startedAt,
          totalDurationSeconds: totalDuration,
          remainingSeconds: totalDuration,
          completed: ordered.length === 0,
          questionDurationsMs: {},
          questionStartedAt: ordered.length > 0 ? startedAt : null,
          summary: null,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to build practice session';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const selectAnswer = useCallback((questionId: string, choice: string) => {
    setSession((current) => {
      if (!current || current.completed) {
        return current;
      }
      const answers = { ...current.answers, [questionId]: choice };
      const reveals = { ...current.reveals };
      const autoReveal =
        current.mode === 'tutor' ||
        (current.mode === 'custom' && current.filters.showExplanationOnSubmit);
      if (autoReveal) {
        reveals[questionId] = true;
      }
      const answeredCount = Object.values(answers).filter(Boolean).length;
      const completed = answeredCount >= current.questions.length;
      return {
        ...current,
        answers,
        reveals,
        completed: completed ? true : current.completed,
      };
    });
  }, []);

  const goToQuestion = useCallback((index: number) => {
    setSession((current) => {
      if (!current) {
        return current;
      }
      const clampedIndex = Math.max(0, Math.min(index, current.questions.length - 1));
      if (clampedIndex === current.currentIndex) {
        return current;
      }
      if (current.completed) {
        return {
          ...current,
          currentIndex: clampedIndex,
        };
      }
      const now = Date.now();
      const activeQuestion = current.questions[current.currentIndex];
      const durations = { ...current.questionDurationsMs };
      if (activeQuestion && current.questionStartedAt !== null) {
        const elapsed = Math.max(0, now - current.questionStartedAt);
        durations[activeQuestion.id] = (durations[activeQuestion.id] ?? 0) + elapsed;
      }
      return {
        ...current,
        currentIndex: clampedIndex,
        questionDurationsMs: durations,
        questionStartedAt: now,
      };
    });
  }, []);

  const revealExplanation = useCallback((questionId: string) => {
    setSession((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        reveals: {
          ...current.reveals,
          [questionId]: true,
        },
      };
    });
  }, []);

  const completeSession = useCallback(() => {
    setSession((current) => {
      if (!current) {
        return current;
      }
      const finalized = finaliseSession(current, Date.now());

      // Record analytics asynchronously (non-blocking)
      if (finalized.summary) {
        recordAnalytics(finalized.summary, finalized.questions, token).catch((err) => {
          console.error('Analytics recording failed:', err);
        });
      }

      return finalized;
    });
  }, [token]);

  const resetSession = useCallback(() => {
    setSession(null);
  }, []);

  const value = useMemo<PracticeSessionContextValue>(() => {
    return {
      session,
      isLoading,
      error,
      filterOptions,
      filtersLoading,
      preview,
      previewTotal,
      previewError,
      previewLoading,
      canLoadMorePreview,
      loadPreview,
      loadMorePreview,
      startSession,
      selectAnswer,
      goToQuestion,
      revealExplanation,
      completeSession,
      resetSession,
    };
  }, [
    completeSession,
    error,
    filterOptions,
    filtersLoading,
    loadMorePreview,
    loadPreview,
    goToQuestion,
    isLoading,
    preview,
    previewError,
    previewLoading,
    previewTotal,
    canLoadMorePreview,
    revealExplanation,
    resetSession,
    selectAnswer,
    session,
    startSession,
  ]);

  return (
    <PracticeSessionContext.Provider value={value}>
      {children}
    </PracticeSessionContext.Provider>
  );
};

export const usePracticeSession = (): PracticeSessionContextValue => {
  const value = useContext(PracticeSessionContext);
  if (!value) {
    throw new Error('usePracticeSession must be used inside a PracticeSessionProvider');
  }
  return value;
};
