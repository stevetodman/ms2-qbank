import { fireEvent, render, screen } from '@testing-library/react';
import { PracticeSummary } from '../components/PracticeSummary';
import type {
  PracticeFilters,
  PracticeSession,
  PracticeSummary as PracticeSummaryData,
  QuestionPayload,
} from '../types/practice';

describe('PracticeSummary component', () => {
  const filters: PracticeFilters = {
    query: undefined,
    tags: [],
    subject: undefined,
    system: undefined,
    status: undefined,
    difficulty: undefined,
    questionCount: 1,
    randomizeOrder: false,
    timePerQuestionSeconds: 60,
    showExplanationOnSubmit: true,
  };

  const question: QuestionPayload = {
    id: 'q1',
    stem: 'Sample question',
    choices: [
      { label: 'A', text: 'Option A' },
      { label: 'B', text: 'Option B' },
    ],
    answer: 'A',
  };

  const summary: PracticeSummaryData = {
    mode: 'timed',
    filters,
    totalQuestions: 1,
    correctCount: 1,
    incorrectCount: 0,
    omittedCount: 0,
    averageTimeSeconds: 30,
    questionPerformances: [
      {
        questionId: 'q1',
        questionIndex: 0,
        selectedAnswer: 'A',
        correctAnswer: 'A',
        correct: true,
        timeSeconds: 30,
      },
    ],
    completedAt: 1,
  };

  const session: PracticeSession = {
    mode: 'timed',
    filters,
    questions: [question],
    answers: { q1: 'A' },
    reveals: { q1: true },
    currentIndex: 0,
    startedAt: 0,
    totalDurationSeconds: 60,
    remainingSeconds: 0,
    completed: true,
    questionDurationsMs: { q1: 30000 },
    questionStartedAt: null,
    summary,
  };

  it('renders summary stats and review controls', () => {
    const onReviewQuestion = jest.fn();
    render(<PracticeSummary session={session} onReviewQuestion={onReviewQuestion} />);

    expect(screen.getByRole('heading', { name: /block summary/i })).toBeInTheDocument();
    expect(screen.getAllByText('Correct')).toHaveLength(2);
    expect(screen.getByText('1 / 1')).toBeInTheDocument();
    expect(screen.getByText('Your answer: A')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /review question/i }));
    expect(onReviewQuestion).toHaveBeenCalledWith(0);
  });
});
