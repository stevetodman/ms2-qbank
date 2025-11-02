import { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { HomeRoute } from '../routes/HomeRoute';

describe('HomeRoute analytics integration', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('fetches analytics on load and refreshes on demand', async () => {
    const firstResponse = {
      generated_at: '2024-07-15T12:00:00Z',
      is_fresh: true,
      artifact: { json_path: '20240715T120000Z.json', markdown_path: '20240715T120000Z.md' },
      metrics: {
        total_questions: 100,
        difficulty_distribution: { Easy: 40, Medium: 40, Hard: 20 },
        review_status_distribution: { Approved: 80, Draft: 15, Archived: 5 },
        usage_summary: {
          tracked_questions: 90,
          total_usage: 200,
          average_usage: 2.2,
          minimum_usage: 0,
          maximum_usage: 12,
          usage_distribution: [
            { deliveries: 0, questions: 10 },
            { deliveries: 1, questions: 20 },
          ],
        },
      },
    };

    const secondResponse = {
      generated_at: '2024-07-16T09:30:00Z',
      is_fresh: false,
      artifact: { json_path: '20240716T093000Z.json', markdown_path: '20240716T093000Z.md' },
      metrics: {
        total_questions: 105,
        difficulty_distribution: { Easy: 35, Medium: 45, Expert: 25 },
        review_status_distribution: { Approved: 70, Draft: 25, Archived: 10 },
        usage_summary: {
          tracked_questions: 95,
          total_usage: 240,
          average_usage: 2.6,
          minimum_usage: 1,
          maximum_usage: 15,
          usage_distribution: [
            { deliveries: 1, questions: 15 },
            { deliveries: 2, questions: 30 },
          ],
        },
      },
    };

    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(firstResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(secondResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

    render(
      <MemoryRouter>
        <HomeRoute />
      </MemoryRouter>
    );

    expect(await screen.findByText(/loading analytics/i)).toBeInTheDocument();

    const difficultyTable = await screen.findByRole('table', { name: /difficulty distribution/i });
    expect(difficultyTable).toBeInTheDocument();
    const statusText = await screen.findByText(/generated/i);
    expect(statusText).toHaveTextContent(/Fresh snapshot/i);

    const refreshButton = await screen.findByRole('button', { name: /refresh metrics/i });
    const user = userEvent.setup();
    await act(async () => {
      await user.click(refreshButton);
    });

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByRole('row', { name: /expert/i })).toBeInTheDocument());
    expect(await screen.findByText(/stale snapshot/i)).toBeInTheDocument();
  });

  it('shows an error message when analytics fail to load', async () => {
    const fetchSpy = jest
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(new Response('error', { status: 500 }));

    render(
      <MemoryRouter>
        <HomeRoute />
      </MemoryRouter>
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Failed to load analytics: Analytics request failed with status 500');

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});
