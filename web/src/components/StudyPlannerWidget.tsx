import type { StudyPlan } from '../api/planner.ts';

interface StudyPlannerWidgetProps {
  plan: StudyPlan | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function formatDateLabel(value: string): string {
  if (!value) {
    return 'Unknown date';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function getDaysUntil(dateString: string): number | null {
  if (!dateString) {
    return null;
  }
  const target = new Date(dateString);
  if (Number.isNaN(target.getTime())) {
    return null;
  }
  const now = new Date();
  const diff = target.getTime() - now.getTime();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function selectUpcomingTasks(plan: StudyPlan | null, count: number): StudyPlan['tasks'] {
  if (!plan) {
    return [];
  }
  const today = new Date();
  const upcoming = plan.tasks.filter((task) => {
    const scheduled = new Date(task.date);
    if (Number.isNaN(scheduled.getTime())) {
      return false;
    }
    return scheduled >= new Date(today.getFullYear(), today.getMonth(), today.getDate());
  });
  const pool = upcoming.length > 0 ? upcoming : plan.tasks;
  return pool.slice(0, count);
}

export const StudyPlannerWidget = ({ plan, loading, error, onRefresh }: StudyPlannerWidgetProps) => {
  const examCountdown = getDaysUntil(plan?.examDate ?? '');
  const nextTasks = selectUpcomingTasks(plan, 3);

  return (
    <section className="card stack">
      <header className="toolbar" style={{ justifyContent: 'space-between', gap: '1rem' }}>
        <div className="stack" style={{ margin: 0 }}>
          <h2>Study planner</h2>
          {plan ? (
            <p>
              Exam on {formatDateLabel(plan.examDate)}
              {typeof examCountdown === 'number' ? ` • ${examCountdown} days remaining` : ''}
            </p>
          ) : (
            <p>Configure a plan to see your personalised roadmap.</p>
          )}
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={() => {
            onRefresh();
          }}
          disabled={loading}
        >
          {loading ? 'Refreshing…' : 'Refresh plan'}
        </button>
      </header>

      {error && (
        <p role="alert" className="error">
          Failed to load planner: {error}
        </p>
      )}

      {loading && <p>Loading planner…</p>}

      {!loading && !plan && !error && <p>No study plan available.</p>}

      {plan && !loading && (
        <div className="stack" style={{ gap: '1.5rem' }}>
          <div
            className="toolbar"
            style={{ flexWrap: 'wrap', gap: '1rem', alignItems: 'stretch' }}
            aria-label="Planner summary"
          >
            <div className="stack" style={{ minWidth: '10rem' }}>
              <span className="badge">Daily focus</span>
              <strong>{plan.dailyStudyHours.toFixed(1)} hrs/day</strong>
            </div>
            <div className="stack" style={{ minWidth: '10rem' }}>
              <span className="badge">Total commitment</span>
              <strong>{plan.totalStudyHours.toFixed(1)} hrs</strong>
            </div>
            <div className="stack" style={{ minWidth: '10rem' }}>
              <span className="badge">Timeline</span>
              <strong>
                {formatDateLabel(plan.startDate)} → {formatDateLabel(plan.examDate)}
              </strong>
            </div>
          </div>

          <div className="stack" style={{ gap: '0.75rem' }} aria-label="Upcoming study blocks">
            <h3>Upcoming focus</h3>
            {nextTasks.length === 0 ? (
              <p>No study blocks scheduled.</p>
            ) : (
              <ul className="stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: '0.5rem' }}>
                {nextTasks.map((task) => (
                  <li key={`${task.date}-${task.subject}`} className="card stack" style={{ padding: '0.75rem' }}>
                    <div className="toolbar" style={{ justifyContent: 'space-between', alignItems: 'baseline' }}>
                      <div className="stack" style={{ gap: '0.25rem' }}>
                        <span className="badge">{formatDateLabel(task.date)}</span>
                        <strong>{task.subject}</strong>
                      </div>
                      <span>{task.hours.toFixed(1)} hrs</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="stack" style={{ gap: '0.75rem' }} aria-label="Subject allocation">
            <h3>Subject priorities</h3>
            {plan.subjectBreakdown.length === 0 ? (
              <p>No subject priorities recorded.</p>
            ) : (
              <ul className="stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: '0.5rem' }}>
                {plan.subjectBreakdown.map((item) => (
                  <li
                    key={item.subject}
                    className="toolbar"
                    style={{ justifyContent: 'space-between', borderBottom: '1px solid var(--border-muted)', paddingBottom: '0.5rem' }}
                  >
                    <span>{item.subject}</span>
                    <span>
                      {item.allocatedHours.toFixed(1)} hrs • {item.percentage.toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
};
