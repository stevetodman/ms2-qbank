import { act, renderHook, waitFor } from '@testing-library/react';
import { PracticeSessionProvider, usePracticeSession } from '../context/PracticeSessionContext.tsx';
import type { PracticeFilters, QuestionPayload } from '../types/practice.ts';

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
});
