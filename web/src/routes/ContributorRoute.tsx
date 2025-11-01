import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchLatestAnalytics, type AnalyticsSnapshot } from '../api/analytics.ts';
import { AnalyticsDashboard } from '../components/AnalyticsDashboard.tsx';

export const ContributorRoute = () => {
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
      const message = err instanceof Error ? err.message : 'Unable to load analytics';
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
    <main className="stack">
      <section className="card stack">
        <header className="toolbar" style={{ justifyContent: 'space-between', gap: '1rem' }}>
          <div className="stack" style={{ margin: 0 }}>
            <h1>Contributor coverage dashboard</h1>
            <p>
              Track progress on optional enrichments like media, references, and review assets to
              ensure the dataset stays production ready.
            </p>
            {generatedLabel && (
              <p>
                Generated {generatedLabel} • {analytics?.isFresh ? 'Fresh' : 'Stale'} snapshot
              </p>
            )}
            {!generatedLabel && !loading && !error && <p>No analytics available.</p>}
          </div>
          <div className="toolbar" style={{ gap: '0.5rem' }}>
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                void loadAnalytics();
              }}
              disabled={loading}
            >
              {loading ? 'Refreshing…' : 'Refresh metrics'}
            </button>
            <Link className="secondary-button" to="/">
              Return home
            </Link>
          </div>
        </header>
        {error && (
          <p role="alert" className="error">
            Failed to load analytics: {error}
          </p>
        )}
      </section>

      <section className="card stack">
        {loading && <p>Loading analytics…</p>}
        {analytics && !loading && <AnalyticsDashboard snapshot={analytics} />}
        {error && (
          <p className="hint">
            Double-check that the analytics generator has produced artifacts in <code>data/analytics</code>.
          </p>
        )}
      </section>
    </main>
  );
};
