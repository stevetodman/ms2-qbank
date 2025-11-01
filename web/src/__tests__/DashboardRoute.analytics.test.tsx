import { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { DashboardRoute } from '../routes/Dashboard.tsx';

describe('DashboardRoute analytics integration', () => {
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

    let analyticsRequestCount = 0;
    jest.spyOn(global, 'fetch').mockImplementation((input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.endsWith('/analytics/latest')) {
        const body = analyticsRequestCount === 0 ? firstResponse : secondResponse;
        analyticsRequestCount += 1;
        return Promise.resolve(
          new Response(JSON.stringify(body), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        );
      }

      if (url.endsWith('/planner/plans')) {
        return Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        );
      }

      throw new Error(`Unexpected fetch for URL ${url}`);
    });

    render(
      <MemoryRouter>
        <DashboardRoute />
      </MemoryRouter>
    );

    expect(await screen.findByText(/loading dashboard data/i)).toBeInTheDocument();

    const metricsHeading = await screen.findByRole('heading', { name: /performance snapshot/i });
    expect(metricsHeading).toBeInTheDocument();
    expect(await screen.findByText(/Fresh data/i)).toBeInTheDocument();
    expect(await screen.findByText(/Overall accuracy/i)).toBeInTheDocument();
    expect(await screen.findByText('100')).toBeInTheDocument();

    const refreshButton = await screen.findByRole('button', { name: /refresh analytics/i });
    const user = userEvent.setup();
    await act(async () => {
      await user.click(refreshButton);
    });

    await waitFor(() => expect(analyticsRequestCount).toBe(2));
    expect(await screen.findByText(/Stale data/i)).toBeInTheDocument();
    expect(await screen.findByText('105')).toBeInTheDocument();
  });

  it('shows an error message when analytics fail to load', async () => {
    let analyticsRequestCount = 0;
    jest.spyOn(global, 'fetch').mockImplementation((input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url.endsWith('/analytics/latest')) {
        analyticsRequestCount += 1;
        return Promise.resolve(new Response('error', { status: 500 }));
      }

      if (url.endsWith('/planner/plans')) {
        return Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        );
      }

      throw new Error(`Unexpected fetch for URL ${url}`);
    });

    render(
      <MemoryRouter>
        <DashboardRoute />
      </MemoryRouter>
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Analytics unavailable: Analytics request failed with status 500');

    expect(analyticsRequestCount).toBe(1);
  });
});
