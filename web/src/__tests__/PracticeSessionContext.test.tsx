import { act, renderHook, waitFor } from '@testing-library/react';
import { PracticeSessionProvider, usePracticeSession } from '../context/PracticeSessionContext.tsx';
import { LAST_SUMMARY_STORAGE_KEY, type PracticeFilters, type QuestionPayload } from '../types/practice.ts';

describe('PracticeSessionContext', () => {
  const sampleQuestion: QuestionPayload = {
    id: 'q1',
    stem: 'Sample stem',
    choices: [
      { label: 'A', text: 'Option A' },
      { label: 'B', text: 'Option B' },
    ],
    answer: 'A',
    explanation: {
      summary: 'Because we said so.',
      rationales: [
        { choice: 'A', text: 'Correct because of evidence.' },
        { choice: 'B', text: 'Incorrect because of evidence.' },
      ],
    },
    metadata: {
      subject: 'Pathology',
      difficulty: 'Medium',
      status: 'Unused',
    },
    tags: ['demo'],
  };

  const baseFilters: PracticeFilters = {
    query: undefined,
    tags: [],
    subject: undefined,
    system: undefined,
    status: undefined,
    difficulty: undefined,
    questionCount: 1,
    randomizeOrder: false,
    timePerQuestionSeconds: 90,
    showExplanationOnSubmit: true,
  };

  beforeEach(() => {
    jest.useFakeTimers();
    window.localStorage.clear();
    const fetchMock = jest.fn();
    (global.fetch as unknown) = fetchMock;
    fetchMock.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            data: [sampleQuestion],
            pagination: { total: 1, limit: 1, offset: 0, returned: 1 },
          }),
      })
    );
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.resetAllMocks();
    window.localStorage.clear();
  });

  it('loads filter metadata on mount', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <PracticeSessionProvider>{children}</PracticeSessionProvider>
    );

    const { result } = renderHook(() => usePracticeSession(), { wrapper });

    await waitFor(() => expect(result.current.filterOptions.subjects).toContain('Pathology'));
  });

  it('creates a tutor mode session and reveals explanations after answering', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <PracticeSessionProvider>{children}</PracticeSessionProvider>
    );

    const { result } = renderHook(() => usePracticeSession(), { wrapper });

    await waitFor(() => expect(result.current.filterOptions.tags).toContain('demo'));

    await act(async () => {
      await result.current.startSession('tutor', baseFilters);
    });

    expect(result.current.session?.questions).toHaveLength(1);
    const question = result.current.session?.questions[0];
    expect(question?.id).toBe('q1');

    act(() => {
      result.current.selectAnswer('q1', 'A');
    });

    expect(result.current.session?.answers['q1']).toBe('A');
    expect(result.current.session?.reveals['q1']).toBe(true);
  });

  it('computes summary data when completing a session', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <PracticeSessionProvider>{children}</PracticeSessionProvider>
    );

    const { result } = renderHook(() => usePracticeSession(), { wrapper });

    await waitFor(() => expect(result.current.filterOptions.tags).toContain('demo'));

    act(() => {
      jest.setSystemTime(new Date('2024-01-01T00:00:00Z'));
    });

    await act(async () => {
      await result.current.startSession('timed', baseFilters);
    });

    expect(result.current.session?.questions).toHaveLength(1);

    act(() => {
      result.current.selectAnswer('q1', 'A');
    });

    act(() => {
      jest.setSystemTime(new Date('2024-01-01T00:00:30Z'));
      result.current.completeSession();
    });

    const summary = result.current.session?.summary;
    expect(summary).toBeTruthy();
    expect(summary?.correctCount).toBe(1);
    expect(summary?.incorrectCount).toBe(0);
    expect(summary?.omittedCount).toBe(0);
    expect(summary?.questionPerformances[0]?.timeSeconds).toBe(30);
    expect(result.current.session?.reveals['q1']).toBe(true);
    expect(result.current.session?.questionStartedAt).toBeNull();

    const stored = window.localStorage.getItem(LAST_SUMMARY_STORAGE_KEY);
    expect(stored).toBeTruthy();
    const parsed = stored ? JSON.parse(stored) : null;
    expect(parsed?.correctCount).toBe(1);
  });
});
