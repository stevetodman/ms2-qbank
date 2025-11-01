import { useCallback, useState } from 'react';
import type {
  AssessmentQuestion,
  AssessmentResponseItem,
  AssessmentSubmissionResponse,
  AssessmentBlueprint,
} from '../api/assessments.ts';
import { createAssessment, startAssessment, submitAssessment } from '../api/assessments.ts';
import { AssessmentSetupForm } from '../components/AssessmentSetupForm.tsx';
import { AssessmentDelivery } from '../components/AssessmentDelivery.tsx';
import { AssessmentSummary } from '../components/AssessmentSummary.tsx';
import { useAssessmentAnalytics } from '../hooks/useAssessmentAnalytics.ts';
import type { AnalyticsSnapshot } from '../api/analytics.ts';

const enum AssessmentStage {
  Setup = 'setup',
  Loading = 'loading',
  Running = 'running',
  Submitting = 'submitting',
  Completed = 'completed',
}

export function SelfAssessmentRoute() {
  const [stage, setStage] = useState<AssessmentStage>(AssessmentStage.Setup);
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [timeLimitSeconds, setTimeLimitSeconds] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timeoutTriggered, setTimeoutTriggered] = useState(false);
  const [submission, setSubmission] = useState<AssessmentSubmissionResponse | null>(null);
  const [analyticsSnapshot, setAnalyticsSnapshot] = useState<AnalyticsSnapshot | null>(null);

  const refreshAnalytics = useAssessmentAnalytics({ onSnapshot: setAnalyticsSnapshot });

  const reset = useCallback(() => {
    setStage(AssessmentStage.Setup);
    setAssessmentId(null);
    setQuestions([]);
    setTimeLimitSeconds(null);
    setError(null);
    setTimeoutTriggered(false);
    setSubmission(null);
    setAnalyticsSnapshot(null);
  }, []);

  const handleSetupSubmit = useCallback(
    async (blueprint: AssessmentBlueprint) => {
      setStage(AssessmentStage.Loading);
      setError(null);
      try {
        const created = await createAssessment(blueprint);
        setAssessmentId(created.assessmentId);
        const started = await startAssessment(created.assessmentId);
        setQuestions(started.questions);
        setTimeLimitSeconds(started.timeLimitSeconds);
        setTimeoutTriggered(false);
        setSubmission(null);
        setAnalyticsSnapshot(null);
        setStage(AssessmentStage.Running);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to start assessment';
        setError(message);
        setStage(AssessmentStage.Setup);
      }
    },
    []
  );

  const handleDeliverySubmit = useCallback(
    async (responses: AssessmentResponseItem[]) => {
      if (!assessmentId) {
        return;
      }
      setStage(AssessmentStage.Submitting);
      try {
        const submitted = await submitAssessment(assessmentId, { responses });
        setSubmission(submitted);
        setStage(AssessmentStage.Completed);
        await refreshAnalytics(submitted);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to submit assessment';
        setError(message);
        setStage(AssessmentStage.Running);
      }
    },
    [assessmentId, refreshAnalytics]
  );

  const handleTimeout = useCallback(() => {
    setTimeoutTriggered(true);
  }, []);

  const busy = stage === AssessmentStage.Loading || stage === AssessmentStage.Submitting;

  return (
    <div className="stack" data-page="self-assessment">
      <h1>Self-assessment</h1>
      {error && (
        <div role="alert">
          <p>{error}</p>
        </div>
      )}
      {stage === AssessmentStage.Setup && <AssessmentSetupForm onSubmit={handleSetupSubmit} busy={busy} />}
      {stage === AssessmentStage.Loading && <p>Preparing assessment…</p>}
      {(stage === AssessmentStage.Running || stage === AssessmentStage.Submitting) && (
        <AssessmentDelivery
          questions={questions}
          timeLimitSeconds={timeLimitSeconds}
          busy={stage === AssessmentStage.Submitting}
          onSubmit={handleDeliverySubmit}
          onTimeout={handleTimeout}
        />
      )}
      {timeoutTriggered && stage !== AssessmentStage.Completed && (
        <p role="status">Time expired. Finalising your responses…</p>
      )}
      {stage === AssessmentStage.Completed && submission && (
        <section>
          <AssessmentSummary submission={submission} onRestart={reset} />
          {analyticsSnapshot ? (
            <p role="status">
              Analytics refreshed {new Date(analyticsSnapshot.generatedAt).toLocaleString()} •{' '}
              {analyticsSnapshot.isFresh ? 'Fresh snapshot' : 'Stale snapshot'}
            </p>
          ) : (
            <p role="status">Analytics refresh scheduled.</p>
          )}
        </section>
      )}
    </div>
  );
}
