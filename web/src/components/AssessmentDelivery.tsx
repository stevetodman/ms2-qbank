import { useEffect, useMemo, useRef, useState } from 'react';
import type {
  AssessmentQuestion,
  AssessmentResponseItem,
} from '../api/assessments.ts';
import { formatSeconds } from '../utils/time.ts';
import { useCountdown } from '../hooks/useCountdown.ts';

interface AssessmentDeliveryProps {
  questions: AssessmentQuestion[];
  timeLimitSeconds: number | null;
  busy?: boolean;
  onSubmit: (responses: AssessmentResponseItem[]) => Promise<void> | void;
  onTimeout?: () => void;
}

export function AssessmentDelivery({
  questions,
  timeLimitSeconds,
  busy = false,
  onSubmit,
  onTimeout,
}: AssessmentDeliveryProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const hasSubmittedRef = useRef(false);

  const secondsRemaining = useCountdown(timeLimitSeconds, !busy && !hasSubmittedRef.current);

  useEffect(() => {
    hasSubmittedRef.current = false;
    setAnswers({});
    setCurrentIndex(0);
  }, [questions]);

  useEffect(() => {
    if (secondsRemaining === 0 && timeLimitSeconds !== null && !hasSubmittedRef.current) {
      hasSubmittedRef.current = true;
      onTimeout?.();
      const responses = buildResponses(questions, answers);
      void Promise.resolve(onSubmit(responses));
    }
  }, [secondsRemaining, timeLimitSeconds, questions, answers, onSubmit, onTimeout]);

  const currentQuestion = questions[currentIndex];
  const total = questions.length;
  const progressLabel = useMemo(() => {
    if (total === 0) {
      return 'No questions loaded';
    }
    return `Question ${currentIndex + 1} of ${total}`;
  }, [currentIndex, total]);

  const handleChoiceSelect = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    if (hasSubmittedRef.current) {
      return;
    }
    hasSubmittedRef.current = true;
    const responses = buildResponses(questions, answers);
    await onSubmit(responses);
  };

  const goToPrevious = () => {
    setCurrentIndex((index) => {
      if (total === 0) {
        return 0;
      }
      return Math.max(0, index - 1);
    });
  };

  const goToNext = () => {
    setCurrentIndex((index) => {
      if (total === 0) {
        return 0;
      }
      return Math.min(total - 1, index + 1);
    });
  };

  const secondsLabel = useMemo(() => formatSeconds(secondsRemaining), [secondsRemaining]);

  return (
    <section aria-label="Assessment delivery">
      <header>
        <h2>{progressLabel}</h2>
        <p role="status">Time remaining: {secondsLabel}</p>
      </header>
      {currentQuestion ? (
        <article>
          <p>{currentQuestion.stem}</p>
          <fieldset disabled={busy}>
            <legend>Answer choices</legend>
            {currentQuestion.choices.map((choice) => {
              const inputId = `${currentQuestion.id}-${choice.label}`;
              const selected = answers[currentQuestion.id] === choice.label;
              return (
                <label key={inputId} htmlFor={inputId}>
                  <input
                    id={inputId}
                    type="radio"
                    name={currentQuestion.id}
                    checked={selected}
                    onChange={() => handleChoiceSelect(currentQuestion.id, choice.label)}
                  />
                  {choice.label}. {choice.text}
                </label>
              );
            })}
          </fieldset>
        </article>
      ) : (
        <p>No questions available.</p>
      )}
      <footer>
        <button type="button" onClick={goToPrevious} disabled={busy || currentIndex === 0}>
          Previous
        </button>
        <button type="button" onClick={goToNext} disabled={busy || total === 0 || currentIndex === total - 1}>
          Next
        </button>
        <button type="button" onClick={handleSubmit} disabled={busy || hasSubmittedRef.current}>
          Submit assessment
        </button>
      </footer>
    </section>
  );
}

function buildResponses(
  questions: AssessmentQuestion[],
  answers: Record<string, string | null>
): AssessmentResponseItem[] {
  return questions.map((question) => ({
    questionId: question.id,
    answer: answers[question.id] ?? null,
  }));
}
