import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { fetchFilterPreview, searchQuestions } from '../api/search.ts';
import type {
  PracticeFilters,
  PracticeMode,
  PracticeSession,
  QuestionPayload,
} from '../types/practice.ts';
import { shuffle } from '../utils/shuffle.ts';

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

function extractFilterOptions(questions: QuestionPayload[]): FilterOptions {
  const subjects = new Set<string>();
  const systems = new Set<string>();
  const statuses = new Set<string>();
  const difficulties = new Set<string>();
  const tags = new Set<string>();

  questions.forEach((question) => {
    if (question.metadata?.subject) {
      subjects.add(question.metadata.subject);
    }
    if (question.metadata?.system) {
      systems.add(question.metadata.system);
    }
    if (question.metadata?.status) {
      statuses.add(question.metadata.status);
    }
    if (question.metadata?.difficulty) {
      difficulties.add(question.metadata.difficulty);
    }
    question.tags?.forEach((tag) => tags.add(tag));
  });

  const toSortedArray = (value: Set<string>) => Array.from(value).sort((a, b) => a.localeCompare(b));

  return {
    subjects: toSortedArray(subjects),
    systems: toSortedArray(systems),
    statuses: toSortedArray(statuses),
    difficulties: toSortedArray(difficulties),
    tags: toSortedArray(tags),
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

export const PracticeSessionProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>(defaultFilterOptions);
  const [filtersLoading, setFiltersLoading] = useState(false);

  useEffect(() => {
    let isActive = true;
    async function loadFilters() {
      setFiltersLoading(true);
      try {
        const preview = await fetchFilterPreview();
        if (!isActive) {
          return;
        }
        setFilterOptions(extractFilterOptions(preview));
      } catch (err) {
        console.error('Failed to preload filter metadata', err);
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
        const completed = nextValue === 0 ? true : current.completed;
        return {
          ...current,
          remainingSeconds: nextValue,
          completed,
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
        const questions = await searchQuestions(filters);
        const ordered = filters.randomizeOrder ? shuffle(questions) : questions;
        const reveals = initialiseReveals(mode, filters, ordered);
        const totalDuration = deriveTotalDuration(mode, filters, ordered.length);
        setSession({
          mode,
          filters,
          questions: ordered,
          answers: {},
          reveals,
          currentIndex: 0,
          startedAt: Date.now(),
          totalDurationSeconds: totalDuration,
          remainingSeconds: totalDuration,
          completed: ordered.length === 0,
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
      if (!current) {
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
      return {
        ...current,
        currentIndex: clampedIndex,
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
      return {
        ...current,
        completed: true,
        remainingSeconds: 0,
      };
    });
  }, []);

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
    goToQuestion,
    isLoading,
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
