import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContributorRoute } from '../routes/ContributorRoute.tsx';

describe('ContributorRoute', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('shows coverage metrics for contributors', async () => {
    const user = userEvent.setup();
    const fetchSpy = jest.spyOn(global, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          generated_at: '2024-07-18T10:00:00Z',
          is_fresh: true,
          artifact: { json_path: 'latest.json', markdown_path: 'latest.md' },
          metrics: {
            total_questions: 42,
            difficulty_distribution: { Easy: 10, Medium: 20, Hard: 12 },
            review_status_distribution: { Unused: 30, Correct: 12 },
            usage_summary: {
              tracked_questions: 40,
              total_usage: 200,
              average_usage: 5,
              minimum_usage: 1,
              maximum_usage: 12,
              usage_distribution: [
                { deliveries: 1, questions: 10 },
                { deliveries: 5, questions: 30 },
              ],
            },
            coverage: [
              {
                label: 'Explanations drafted',
                completed: 42,
                missing: 0,
                total: 42,
                coverage: 1,
              },
              {
                label: 'Media attachments added',
                completed: 21,
                missing: 21,
                total: 42,
                coverage: 0.5,
              },
              {
                label: 'Media alt text provided',
                completed: 21,
                missing: 0,
                total: 21,
                coverage: 1,
              },
            ],
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    render(
      <MemoryRouter>
        <ContributorRoute />
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /contributor coverage dashboard/i })).toBeInTheDocument();
    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    expect(await screen.findByText(/Media attachments added/)).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText(/Media alt text provided/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /refresh metrics/i }));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
  });
});
