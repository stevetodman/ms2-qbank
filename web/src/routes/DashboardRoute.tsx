import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchLatestAnalytics, type AnalyticsSnapshot } from '../api/analytics.ts';
import { fetchStudyPlans, type StudyPlan } from '../api/planner.ts';
import { AnalyticsDashboard } from '../components/AnalyticsDashboard.tsx';
import { StudyPlannerWidget } from '../components/StudyPlannerWidget.tsx';
import { LAST_SUMMARY_STORAGE_KEY, type PracticeSummary } from '../types/practice.ts';
import { formatSeconds } from '../utils/time.ts';

export const DashboardRoute = () => {
  const [recentSummary, setRecentSummary] = useState<PracticeSummary | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSnapshot | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  const [planner, setPlanner] = useState<StudyPlan | null>(null);
  const [loadingPlanner, setLoadingPlanner] = useState(false);
  const [plannerError, setPlannerError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = window.localStorage?.getItem(LAST_SUMMARY_STORAGE_KEY);
      if (!raw) {
        setRecentSummary(null);
        return;
      }
      const parsed = JSON.parse(raw) as PracticeSummary;
      setRecentSummary(parsed);
    } catch (err) {
      console.warn('Unable to read practice summary', err);
      setRecentSummary(null);
    }
  }, []);

  const loadAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    setAnalyticsError(null);
    try {
      const snapshot = await fetchLatestAnalytics();
      setAnalytics(snapshot);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load analytics';
      setAnalyticsError(message);
    } finally {
      setLoadingAnalytics(false);
    }
  }, []);

  const loadPlanner = useCallback(async () => {
    setLoadingPlanner(true);
    setPlannerError(null);
    try {
      const plans = await fetchStudyPlans();
      setPlanner(plans[0] ?? null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load study plan';
      setPlannerError(message);
    } finally {
      setLoadingPlanner(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  useEffect(() => {
    void loadPlanner();
  }, [loadPlanner]);

  const generatedLabel = analytics?.generatedAt
    ? new Date(analytics.generatedAt).toLocaleString()
    : null;

  return (
    <div className="stack" data-page="dashboard">
      <section className="card stack">
        <header>
          <h1>MS2 QBank Learner Experience</h1>
          <p>
            Build focused practice sessions, take questions in timed or tutor mode, and log review
            actions without leaving the browser. This early web client connects to the FastAPI search
            and review services shipped in the backend to provide an end-to-end learner workflow.
          </p>
        </header>
        <div className="stack">
          <h2>What can you do today?</h2>
          <ul>
            <li>Create a personalised practice block with rich filters and delivery modes.</li>
            <li>Answer questions with immediate or deferred explanations based on your mode.</li>
            <li>Bookmark, tag, and request editorial review directly from the question surface.</li>
            <li>Review the audit history for every question to understand outstanding actions.</li>
            <li>Browse the medical library for concise refreshers connected to question topics.</li>
            <li>Capture notebook entries and link them to question reviews for rapid follow-up.</li>
          </ul>
        </div>
        <footer className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
          <Link className="primary-button" to="/qbank">
            Launch Practice Workspace
          </Link>
          <Link className="secondary-button" to="/library">
            Explore medical library
          </Link>
          <Link className="secondary-button" to="/notebook">
            Open learner notebook
          </Link>
        </footer>
      </section>

      <StudyPlannerWidget
        plan={planner}
        loading={loadingPlanner}
        error={plannerError}
        onRefresh={() => {
          void loadPlanner();
        }}
      />

      <section className="card stack">
        <header className="toolbar" style={{ justifyContent: 'space-between', gap: '1rem' }}>
          <div className="stack" style={{ margin: 0 }}>
            <h2>Analytics snapshot</h2>
            {generatedLabel && (
              <p>
                Generated {generatedLabel} • {analytics?.isFresh ? 'Fresh' : 'Stale'} snapshot
              </p>
            )}
            {!generatedLabel && !loadingAnalytics && !analyticsError && <p>No analytics available.</p>}
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              void loadAnalytics();
            }}
            disabled={loadingAnalytics}
          >
            {loadingAnalytics ? 'Refreshing…' : 'Refresh metrics'}
          </button>
        </header>
        {loadingAnalytics && <p>Loading analytics…</p>}
        {analyticsError && (
          <p role="alert" className="error">
            Failed to load analytics: {analyticsError}
          </p>
        )}
        {analytics && !loadingAnalytics && <AnalyticsDashboard snapshot={analytics} />}
      </section>

      {recentSummary && (
        <section className="card stack">
          <header className="stack">
            <h2>Recent performance</h2>
            <p>
              Completed {new Date(recentSummary.completedAt).toLocaleString()} •{' '}
              {recentSummary.mode.toUpperCase()} ({recentSummary.totalQuestions} questions)
            </p>
          </header>
          <div className="toolbar" style={{ flexWrap: 'wrap', gap: '1rem' }}>
            <div className="stack">
              <span className="badge">Correct</span>
              <strong>
                {recentSummary.correctCount} / {recentSummary.totalQuestions}
              </strong>
            </div>
            <div className="stack">
              <span className="badge">Incorrect</span>
              <strong>{recentSummary.incorrectCount}</strong>
            </div>
            <div className="stack">
              <span className="badge">Omitted</span>
              <strong>{recentSummary.omittedCount}</strong>
            </div>
            <div className="stack">
              <span className="badge">Average time</span>
              <strong>{formatSeconds(recentSummary.averageTimeSeconds)}</strong>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
