import { useMemo } from 'react';
import { usePracticeSession } from '../context/PracticeSessionContext.tsx';
import { formatSeconds } from '../utils/time.ts';
import { QuestionViewer } from './QuestionViewer.tsx';
import { ReviewSidebar } from './ReviewSidebar.tsx';
import { PracticeSummary } from './PracticeSummary.tsx';

export const PracticeWorkspace = () => {
  const { session, selectAnswer, goToQuestion, revealExplanation, completeSession } = usePracticeSession();

  const activeQuestion = useMemo(() => {
    if (!session || session.questions.length === 0) {
      return null;
    }
    const question = session.questions[session.currentIndex];
    const answer = session.answers[question.id];
    const revealState = session.reveals[question.id] ?? false;
    const hasAnswered = Boolean(answer);
    const explanationVisible =
      revealState ||
      session.completed ||
      (session.mode === 'tutor' && hasAnswered) ||
      (session.mode === 'custom' && session.filters.showExplanationOnSubmit && hasAnswered);
    const canReveal = hasAnswered && !explanationVisible && (session.mode !== 'timed' || session.completed);
    return {
      question,
      answer,
      revealState,
      explanationVisible,
      canReveal,
    };
  }, [session]);

  if (!session) {
    return null;
  }

  const totalQuestions = session.questions.length;
  const progress = totalQuestions === 0 ? 0 : Math.round(((session.currentIndex + 1) / totalQuestions) * 100);

  return (
    <section className="stack" id="workspace">
      {session.summary && (
        <PracticeSummary session={session} onReviewQuestion={goToQuestion} />
      )}
      {activeQuestion && (
        <>
          <header className="card stack">
            <div className="toolbar" style={{ justifyContent: 'space-between' }}>
              <div className="stack" style={{ gap: '0.25rem' }}>
                <strong>Active block</strong>
                <span>{session.mode.toUpperCase()} • {session.questions.length} questions</span>
              </div>
              {session.totalDurationSeconds !== null && (
                <div className="stack" style={{ alignItems: 'flex-end', gap: '0.25rem' }}>
                  <span className="badge">Time remaining</span>
                  <span className="timer">{formatSeconds(session.remainingSeconds)} / {formatSeconds(session.totalDurationSeconds)}</span>
                </div>
              )}
            </div>
            <progress
              value={progress}
              max={100}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progress}
            />
            <div className="toolbar">
              <button type="button" onClick={() => goToQuestion(session.currentIndex - 1)} disabled={session.currentIndex === 0}>
                Previous
              </button>
              <button
                type="button"
                onClick={() => goToQuestion(session.currentIndex + 1)}
                disabled={session.currentIndex >= totalQuestions - 1}
              >
                Next
              </button>
              <button type="button" onClick={completeSession} disabled={session.completed}>
                End block
              </button>
            </div>
          </header>
          <div className="stack" style={{ gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}>
              <div style={{ flex: '1 1 60%', minWidth: '320px' }}>
                <QuestionViewer
                  question={activeQuestion.question}
                  mode={session.mode}
                  answer={activeQuestion.answer}
                  revealed={activeQuestion.revealState}
                  completed={session.completed}
                  onSelect={(choice) => selectAnswer(activeQuestion.question.id, choice)}
                  onReveal={() => revealExplanation(activeQuestion.question.id)}
                  canReveal={activeQuestion.canReveal}
                  questionNumber={session.currentIndex + 1}
                  totalQuestions={totalQuestions}
                />
              </div>
              <div style={{ flex: '1 1 30%', minWidth: '280px' }}>
                <ReviewSidebar questionId={activeQuestion.question.id} mode={session.mode} />
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
};
