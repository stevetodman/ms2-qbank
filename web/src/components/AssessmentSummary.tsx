import type { AssessmentSubmissionResponse } from '../api/assessments';

interface AssessmentSummaryProps {
  submission: AssessmentSubmissionResponse;
  onRestart?: () => void;
}

export function AssessmentSummary({ submission, onRestart }: AssessmentSummaryProps) {
  const completedAt = new Date(submission.submittedAt).toLocaleString();
  const { score } = submission;

  return (
    <section aria-label="Assessment summary">
      <header>
        <h2>Assessment complete</h2>
        <p>Completed at {completedAt}</p>
      </header>
      <dl>
        <div>
          <dt>Total questions</dt>
          <dd>{score.totalQuestions}</dd>
        </div>
        <div>
          <dt>Correct</dt>
          <dd>{score.correct}</dd>
        </div>
        <div>
          <dt>Incorrect</dt>
          <dd>{score.incorrect}</dd>
        </div>
        <div>
          <dt>Omitted</dt>
          <dd>{score.omitted}</dd>
        </div>
        <div>
          <dt>Score</dt>
          <dd>{score.percentage.toFixed(2)}%</dd>
        </div>
        <div>
          <dt>Time spent</dt>
          <dd>{score.durationSeconds === null ? '—' : `${score.durationSeconds} seconds`}</dd>
        </div>
      </dl>
      {onRestart && (
        <button type="button" onClick={onRestart}>
          Start another assessment
        </button>
      )}
    </section>
  );
}
