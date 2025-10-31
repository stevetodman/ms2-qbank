import { render, screen, within } from '@testing-library/react';
import type { AnalyticsSnapshot } from '../api/analytics.ts';
import { AnalyticsDashboard } from '../components/AnalyticsDashboard.tsx';

describe('AnalyticsDashboard', () => {
  const snapshot: AnalyticsSnapshot = {
    generatedAt: '2024-07-15T12:00:00Z',
    isFresh: true,
    artifact: { jsonPath: '20240715T120000Z.json', markdownPath: '20240715T120000Z.md' },
    metrics: {
      totalQuestions: 120,
      difficultyDistribution: {
        Easy: 40,
        Medium: 60,
        Hard: 20,
      },
      reviewStatusDistribution: {
        Approved: 80,
        Draft: 30,
        Archived: 10,
      },
      usageSummary: {
        trackedQuestions: 100,
        totalUsage: 250,
        averageUsage: 2.5,
        minimumUsage: 0,
        maximumUsage: 10,
        usageDistribution: [
          { deliveries: 0, questions: 5 },
          { deliveries: 1, questions: 20 },
          { deliveries: 5, questions: 10 },
        ],
      },
    },
  };

  it('renders difficulty and review tables with counts', () => {
    render(<AnalyticsDashboard snapshot={snapshot} />);

    const difficultyTable = screen.getByRole('table', { name: /difficulty distribution/i });
    expect(within(difficultyTable).getByRole('row', { name: /easy/i })).toBeInTheDocument();
    expect(within(difficultyTable).getByText('40')).toBeInTheDocument();

    const reviewTable = screen.getByRole('table', { name: /review status distribution/i });
    expect(within(reviewTable).getByRole('row', { name: /approved/i })).toBeInTheDocument();
    expect(within(reviewTable).getByText('80')).toBeInTheDocument();
  });

  it('renders usage metrics and distribution', () => {
    render(<AnalyticsDashboard snapshot={snapshot} />);

    const metricsTable = screen.getByRole('table', { name: /usage metrics/i });
    expect(within(metricsTable).getByText(/tracked questions/i)).toBeInTheDocument();
    expect(within(metricsTable).getByText('250')).toBeInTheDocument();

    const distributionTable = screen.getByRole('table', { name: /usage distribution/i });
    expect(within(distributionTable).getAllByRole('row')).toHaveLength(4); // header + 3 rows
    expect(within(distributionTable).getByRole('row', { name: /5 10/i })).toBeInTheDocument();
  });
});
