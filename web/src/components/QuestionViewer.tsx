import clsx from 'clsx';
import type { PracticeMode, QuestionPayload } from '../types/practice.ts';

interface QuestionViewerProps {
  question: QuestionPayload;
  mode: PracticeMode;
  answer?: string;
  revealed: boolean;
  completed: boolean;
  onSelect: (choice: string) => void;
  onReveal: () => void;
  canReveal: boolean;
  questionNumber: number;
  totalQuestions: number;
}

export const QuestionViewer = ({
  question,
  mode,
  answer,
  revealed,
  completed,
  onSelect,
  onReveal,
  canReveal,
  questionNumber,
  totalQuestions,
}: QuestionViewerProps) => {
  const explanationVisible = revealed || completed;
  const modeLabel = mode === 'tutor' ? 'Tutor mode' : mode === 'timed' ? 'Timed mode' : 'Custom mode';

  return (
    <article className="stack">
      <header className="stack">
        <div className="toolbar" style={{ justifyContent: 'space-between' }}>
          <span className="badge">Question {questionNumber} of {totalQuestions}</span>
          <span className="badge">{modeLabel}</span>
        </div>
        <h2>{question.stem}</h2>
        {question.metadata && (
          <div className="toolbar">
            {question.metadata.subject && <span className="badge">Subject: {question.metadata.subject}</span>}
            {question.metadata.system && <span className="badge">System: {question.metadata.system}</span>}
            {question.metadata.difficulty && (
              <span className="badge">Difficulty: {question.metadata.difficulty}</span>
            )}
            {question.metadata.status && <span className="badge">Status: {question.metadata.status}</span>}
          </div>
        )}
        {question.tags && question.tags.length > 0 && (
          <div className="toolbar">
            {question.tags.map((tag) => (
              <span key={tag} className="badge">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </header>
      <section className="stack">
        {question.choices.map((choice) => {
          const selected = answer === choice.label;
          const isCorrect = explanationVisible && question.answer === choice.label;
          const isIncorrect = explanationVisible && selected && question.answer !== choice.label;
          const className = clsx('choice-card', {
            selected,
            correct: isCorrect,
            incorrect: isIncorrect,
          });
          return (
            <button
              key={choice.label}
              type="button"
              className={className}
              onClick={() => onSelect(choice.label)}
              disabled={completed}
            >
              <strong>{choice.label}.</strong> {choice.text}
            </button>
          );
        })}
      </section>
      <footer className="stack">
        <div className="toolbar">
          <button type="button" onClick={onReveal} disabled={!canReveal}>
            Reveal explanation
          </button>
          {!canReveal && !explanationVisible && mode === 'timed' && <span>Complete the block to see explanations.</span>}
        </div>
        {explanationVisible && question.explanation && (
          <section className="card stack">
            <h3>Explanation</h3>
            <p>{question.explanation.summary}</p>
            {question.explanation.rationales && question.explanation.rationales.length > 0 && (
              <ul>
                {question.explanation.rationales.map((rationale) => (
                  <li key={rationale.choice}>
                    <strong>{rationale.choice}:</strong> {rationale.text}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </footer>
    </article>
  );
};
