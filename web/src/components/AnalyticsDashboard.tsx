import type { AnalyticsSnapshot } from '../api/analytics';

interface AnalyticsDashboardProps {
  snapshot: AnalyticsSnapshot;
}

function formatCount(value: number): string {
  return value.toLocaleString();
}

function renderDistributionRows(distribution: Record<string, number>) {
  const entries = Object.entries(distribution).sort(([a], [b]) => a.localeCompare(b));
  if (entries.length === 0) {
    return (
      <tr>
        <td colSpan={2}>No data available</td>
      </tr>
    );
  }

  return entries.map(([label, value]) => (
    <tr key={label}>
      <th scope="row">{label}</th>
      <td>{formatCount(value)}</td>
    </tr>
  ));
}

export function AnalyticsDashboard({ snapshot }: AnalyticsDashboardProps) {
  const { metrics } = snapshot;
  const usageSummary = metrics.usageSummary;

  return (
    <div className="stack" aria-live="polite">
      <table className="data-table">
        <caption>Difficulty distribution</caption>
        <thead>
          <tr>
            <th scope="col">Difficulty</th>
            <th scope="col">Questions</th>
          </tr>
        </thead>
        <tbody>{renderDistributionRows(metrics.difficultyDistribution)}</tbody>
      </table>

      <table className="data-table">
        <caption>Review status distribution</caption>
        <thead>
          <tr>
            <th scope="col">Status</th>
            <th scope="col">Questions</th>
          </tr>
        </thead>
        <tbody>{renderDistributionRows(metrics.reviewStatusDistribution)}</tbody>
      </table>

      <table className="data-table">
        <caption>Usage metrics</caption>
        <tbody>
          <tr>
            <th scope="row">Tracked questions</th>
            <td>{formatCount(usageSummary.trackedQuestions)}</td>
          </tr>
          <tr>
            <th scope="row">Total deliveries</th>
            <td>{formatCount(usageSummary.totalUsage)}</td>
          </tr>
          <tr>
            <th scope="row">Average deliveries</th>
            <td>{usageSummary.averageUsage.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
          </tr>
          <tr>
            <th scope="row">Minimum deliveries</th>
            <td>{formatCount(usageSummary.minimumUsage)}</td>
          </tr>
          <tr>
            <th scope="row">Maximum deliveries</th>
            <td>{formatCount(usageSummary.maximumUsage)}</td>
          </tr>
        </tbody>
      </table>

      <table className="data-table">
        <caption>Usage distribution</caption>
        <thead>
          <tr>
            <th scope="col">Deliveries</th>
            <th scope="col">Questions</th>
          </tr>
        </thead>
        <tbody>
          {usageSummary.usageDistribution.length === 0 ? (
            <tr>
              <td colSpan={2}>No data available</td>
            </tr>
          ) : (
            usageSummary.usageDistribution.map((bucket) => (
              <tr key={bucket.deliveries}>
                <th scope="row">{formatCount(bucket.deliveries)}</th>
                <td>{formatCount(bucket.questions)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
