import { act, renderHook, waitFor } from '@testing-library/react';
import { PracticeSessionProvider, usePracticeSession } from '../context/PracticeSessionContext';
import { LAST_SUMMARY_STORAGE_KEY, type PracticeFilters, type QuestionPayload } from '../types/practice';

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
    fetchMock.mockImplementation((input?: RequestInfo, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input?.toString() ?? '';
      if (url.endsWith('/filters')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              subjects: ['Pathology'],
              systems: [],
              statuses: ['Unused'],
              difficulties: ['Medium'],
              tags: ['demo'],
            }),
        });
      }

      if (url.endsWith('/search')) {
        const body = init?.body ? JSON.parse(init.body.toString()) : {};
        if (body.limit === 10 && body.offset === 0) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                data: [sampleQuestion],
                pagination: { total: 2, limit: 10, offset: 0, returned: 1 },
              }),
          });
        }
        if (body.limit === 10 && body.offset === 1) {
          const extraQuestion: QuestionPayload = {
            ...sampleQuestion,
            id: 'q2',
            stem: 'Another preview stem',
          };
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                data: [extraQuestion],
                pagination: { total: 2, limit: 10, offset: 1, returned: 1 },
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              data: [sampleQuestion],
              pagination: { total: 1, limit: body.limit ?? 1, offset: body.offset ?? 0, returned: 1 },
            }),
        });
      }

      throw new Error(`Unexpected fetch call to ${url}`);
    });
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

  it('loads preview data in pages', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <PracticeSessionProvider>{children}</PracticeSessionProvider>
    );

    const { result } = renderHook(() => usePracticeSession(), { wrapper });

    await waitFor(() => expect(result.current.filterOptions.tags).toContain('demo'));

    await act(async () => {
      await result.current.loadPreview(baseFilters);
    });

    await waitFor(() => expect(result.current.preview).toHaveLength(1));
    expect(result.current.previewTotal).toBe(2);

    await act(async () => {
      await result.current.loadMorePreview();
    });

    await waitFor(() => expect(result.current.preview).toHaveLength(2));
    expect(result.current.canLoadMorePreview).toBe(false);
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
