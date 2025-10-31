import { useMemo } from 'react';
import { usePracticeSession } from '../context/PracticeSessionContext.tsx';
import { formatSeconds } from '../utils/time.ts';
import { QuestionViewer } from './QuestionViewer.tsx';
import { ReviewSidebar } from './ReviewSidebar.tsx';

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

  if (!session || !activeQuestion) {
    return null;
  }

  const { question, answer, revealState, canReveal } = activeQuestion;
  const total = session.questions.length;
  const currentNumber = session.currentIndex + 1;
  const progress = total === 0 ? 0 : Math.round((currentNumber / total) * 100);
  const timeRemaining = formatSeconds(session.remainingSeconds);
  const totalTime = formatSeconds(session.totalDurationSeconds);

  const goPrevious = () => goToQuestion(session.currentIndex - 1);
  const goNext = () => goToQuestion(session.currentIndex + 1);

  return (
    <section className="stack" id="workspace">
      <header className="card stack">
        <div className="toolbar" style={{ justifyContent: 'space-between' }}>
          <div className="stack" style={{ gap: '0.25rem' }}>
            <strong>Active block</strong>
            <span>{session.mode.toUpperCase()} • {total} questions</span>
          </div>
          {session.totalDurationSeconds !== null && (
            <div className="stack" style={{ alignItems: 'flex-end', gap: '0.25rem' }}>
              <span className="badge">Time remaining</span>
              <span className="timer">{timeRemaining} / {totalTime}</span>
            </div>
          )}
        </div>
        <progress value={progress} max={100} aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} />
        <div className="toolbar">
          <button type="button" onClick={goPrevious} disabled={session.currentIndex === 0}>
            Previous
          </button>
          <button type="button" onClick={goNext} disabled={session.currentIndex >= total - 1}>
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
              question={question}
              mode={session.mode}
              answer={answer}
              revealed={revealState}
              completed={session.completed}
              onSelect={(choice) => selectAnswer(question.id, choice)}
              onReveal={() => revealExplanation(question.id)}
              canReveal={canReveal}
              questionNumber={currentNumber}
              totalQuestions={total}
            />
          </div>
          <div style={{ flex: '1 1 30%', minWidth: '280px' }}>
            <ReviewSidebar questionId={question.id} mode={session.mode} />
          </div>
        </div>
      </div>
    </section>
  );
};
