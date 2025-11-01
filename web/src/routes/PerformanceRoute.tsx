import { useCallback, useEffect, useState } from 'react';
import { fetchLatestAnalytics, type AnalyticsSnapshot } from '../api/analytics.ts';
import { AnalyticsDashboard } from '../components/AnalyticsDashboard.tsx';

export const PerformanceRoute = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const snapshot = await fetchLatestAnalytics();
      setAnalytics(snapshot);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load performance analytics';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  const generatedLabel = analytics?.generatedAt
    ? new Date(analytics.generatedAt).toLocaleString()
    : null;

  return (
    <div className="stack" data-page="performance">
      <section className="card stack">
        <header className="stack">
          <h1>Performance insights</h1>
          <p>
            Track your accuracy, pacing, and review actions across practice and assessments. Use the
            analytics below to identify weak systems, climb your percentile ranks, and plan your next
            study block.
          </p>
        </header>
        <div className="toolbar" style={{ justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            {generatedLabel ? (
              <p>
                Snapshot generated {generatedLabel} • {analytics?.isFresh ? 'Fresh' : 'Stale'}
              </p>
            ) : (
              <p>Snapshot pending. Run a practice block or assessment to populate analytics.</p>
            )}
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              void loadAnalytics();
            }}
            disabled={loading}
          >
            {loading ? 'Refreshing…' : 'Refresh analytics'}
          </button>
        </div>
      </section>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {loading && <p role="status">Loading analytics…</p>}
      {analytics && !loading && <AnalyticsDashboard snapshot={analytics} />}
    </div>
  );
};
