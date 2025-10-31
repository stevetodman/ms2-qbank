import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LAST_SUMMARY_STORAGE_KEY, type PracticeSummary } from '../types/practice.ts';
import { formatSeconds } from '../utils/time.ts';

export const HomeRoute = () => {
  const [recentSummary, setRecentSummary] = useState<PracticeSummary | null>(null);

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

  return (
    <main>
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
          </ul>
        </div>
        <footer>
          <Link className="primary-button" to="/practice">
            Launch Practice Workspace
          </Link>
        </footer>
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
    </main>
  );
};
