import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AssessmentRoute } from '../routes/AssessmentRoute.tsx';

describe('AssessmentRoute', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('guides a learner through the full assessment workflow', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch').mockImplementation((input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url === '/api/assessments') {
        return Promise.resolve(
          new Response(
            JSON.stringify({ assessment_id: 'asm-1', question_count: 160, status: 'created' }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        );
      }
      if (url === '/api/assessments/asm-1/start') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              assessment_id: 'asm-1',
              started_at: '2024-07-16T10:00:00Z',
              expires_at: '2024-07-16T12:00:00Z',
              time_limit_seconds: 120,
              questions: [
                {
                  id: 'q1',
                  stem: 'Example question stem',
                  choices: [
                    { label: 'A', text: 'Option A' },
                    { label: 'B', text: 'Option B' },
                  ],
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        );
      }
      if (url === '/api/assessments/asm-1/submit') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              assessment_id: 'asm-1',
              submitted_at: '2024-07-16T12:05:00Z',
              score: {
                total_questions: 160,
                correct: 120,
                incorrect: 30,
                omitted: 10,
                percentage: 75,
                duration_seconds: 7199,
              },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        );
      }
      if (url === '/api/analytics/analytics/latest') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              generated_at: '2024-07-16T12:10:00Z',
              is_fresh: true,
              artifact: { json_path: '20240716T121000Z.json', markdown_path: '20240716T121000Z.md' },
              metrics: {
                total_questions: 200,
                difficulty_distribution: { Easy: 80, Medium: 80, Hard: 40 },
                review_status_distribution: { Approved: 150, Draft: 30, Archived: 20 },
                usage_summary: {
                  tracked_questions: 180,
                  total_usage: 400,
                  average_usage: 2.22,
                  minimum_usage: 0,
                  maximum_usage: 15,
                  usage_distribution: [
                    { deliveries: 0, questions: 20 },
                    { deliveries: 1, questions: 60 },
                  ],
                },
              },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        );
      }
      return Promise.reject(new Error(`Unexpected fetch for URL ${url}`));
    });

    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <AssessmentRoute />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/candidate identifier/i), 'Candidate-999');
    await user.click(screen.getByRole('button', { name: /begin assessment/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('/api/assessments', expect.anything()));

    expect(await screen.findByText(/example question stem/i)).toBeInTheDocument();

    await user.click(screen.getByLabelText(/A\. Option A/));
    await user.click(screen.getByRole('button', { name: /submit assessment/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('/api/assessments/asm-1/submit', expect.anything()));

    expect(await screen.findByRole('heading', { name: /assessment complete/i })).toBeInTheDocument();
    expect(screen.getByText('75.00%')).toBeInTheDocument();

    await waitFor(() => expect(fetchSpy.mock.calls.length).toBeGreaterThanOrEqual(4));
    const analyticsCall = fetchSpy.mock.calls.find(([url]) => url === '/api/analytics/analytics/latest');
    expect(analyticsCall).toBeDefined();
    expect(await screen.findByText(/Analytics refreshed/i)).toBeInTheDocument();
  });
});
