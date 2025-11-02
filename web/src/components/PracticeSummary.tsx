import type { PracticeSession, PracticeSummary as PracticeSummaryData } from '../types/practice';
import { formatSeconds } from '../utils/time';

interface PracticeSummaryProps {
  session: PracticeSession;
  onReviewQuestion: (index: number) => void;
}

function getStatus(performance: PracticeSummaryData['questionPerformances'][number] | undefined) {
  if (!performance) {
    return 'Omitted';
  }
  if (!performance.selectedAnswer) {
    return 'Omitted';
  }
  return performance.correct ? 'Correct' : 'Incorrect';
}

export const PracticeSummary = ({ session, onReviewQuestion }: PracticeSummaryProps) => {
  const summary = session.summary;
  if (!summary) {
    return null;
  }

  const performanceById = new Map(
    summary.questionPerformances.map((performance) => [performance.questionId, performance])
  );

  const averageTimeLabel = formatSeconds(summary.averageTimeSeconds);

  return (
    <section className="card stack" aria-label="Practice summary">
      <header className="stack">
        <h2>Block summary</h2>
        <p>
          Completed {new Date(summary.completedAt).toLocaleString()} • {summary.mode.toUpperCase()}
        </p>
      </header>
      <div className="toolbar" style={{ flexWrap: 'wrap', gap: '1rem' }}>
        <div className="stack">
          <span className="badge">Correct</span>
          <strong>
            {summary.correctCount} / {summary.totalQuestions}
          </strong>
        </div>
        <div className="stack">
          <span className="badge">Incorrect</span>
          <strong>{summary.incorrectCount}</strong>
        </div>
        <div className="stack">
          <span className="badge">Omitted</span>
          <strong>{summary.omittedCount}</strong>
        </div>
        <div className="stack">
          <span className="badge">Average time</span>
          <strong>{averageTimeLabel}</strong>
        </div>
      </div>
      <div className="stack" style={{ gap: '0.75rem' }}>
        <h3>Review questions</h3>
        {session.questions.length === 0 ? (
          <p>No questions were delivered in this block.</p>
        ) : (
          <ul className="stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: '0.75rem' }}>
            {session.questions.map((question, index) => {
              const performance = performanceById.get(question.id);
              const status = getStatus(performance);
              const timeLabel = formatSeconds(performance?.timeSeconds ?? 0);
              return (
                <li key={question.id} className="card stack" style={{ padding: '0.75rem' }}>
                  <div className="toolbar" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="stack" style={{ gap: '0.25rem' }}>
                      <span className="badge">Question {index + 1}</span>
                      <strong>{status}</strong>
                      {performance?.selectedAnswer && (
                        <span>Your answer: {performance.selectedAnswer}</span>
                      )}
                      {!performance?.selectedAnswer && <span>No answer submitted</span>}
                      <span>Time: {timeLabel}</span>
                    </div>
                    <button type="button" onClick={() => onReviewQuestion(index)}>
                      Review question
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
};
