import type { QuestionPayload } from '../types/practice';
import type { CardCreate } from '../api/flashcards';

/**
 * Convert a QBank question to a flashcard format
 */
export function questionToFlashcard(question: QuestionPayload, deckId: number): CardCreate {
  // Find the correct answer choice text
  const correctChoice = question.choices.find((c) => c.label === question.answer);
  const correctAnswerText = correctChoice ? `${correctChoice.label}. ${correctChoice.text}` : question.answer;

  // Build the front (question)
  const front = question.stem;

  // Build the back (answer + explanation)
  let back = `**Correct Answer: ${correctAnswerText}**\n\n`;

  if (question.explanation?.summary) {
    back += `${question.explanation.summary}\n\n`;
  }

  // Add metadata tags for context
  const tags: string[] = [];
  if (question.metadata?.subject) tags.push(question.metadata.subject);
  if (question.metadata?.system) tags.push(question.metadata.system);
  if (tags.length > 0) {
    back += `\n_${tags.join(' • ')}_`;
  }

  return {
    deck_id: deckId,
    front,
    back,
    source_question_id: question.id,
  };
}

/**
 * Get a summary of what will be on the flashcard
 */
export function getFlashcardPreview(question: QuestionPayload): {
  front: string;
  back: string;
} {
  const correctChoice = question.choices.find((c) => c.label === question.answer);
  const correctAnswerText = correctChoice ? `${correctChoice.label}. ${correctChoice.text}` : question.answer;

  return {
    front: question.stem,
    back: `**${correctAnswerText}**\n\n${question.explanation?.summary || ''}`,
  };
}
