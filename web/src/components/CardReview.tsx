import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import * as flashcardApi from '../api/flashcards';
import '../styles/flashcards.css';

interface CardReviewProps {
  deckId: number;
  onComplete?: () => void;
}

export function CardReview({ deckId, onComplete }: CardReviewProps) {
  const { token } = useAuth();
  const [dueCards, setDueCards] = useState<flashcardApi.DueCard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    loadDueCards();
  }, [deckId, token]);

  const loadDueCards = async () => {
    try {
      setLoading(true);
      setError(null);
      const cards = await flashcardApi.getDueCards(deckId, undefined, token || undefined);
      setDueCards(cards);
      setCurrentIndex(0);
      setIsFlipped(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cards');
    } finally {
      setLoading(false);
    }
  };

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleRating = async (quality: number) => {
    if (!dueCards[currentIndex] || reviewing) return;

    try {
      setReviewing(true);
      const currentCard = dueCards[currentIndex];

      await flashcardApi.submitReview(
        {
          card_id: currentCard.card.id,
          quality,
        },
        token || undefined
      );

      // Move to next card
      if (currentIndex < dueCards.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setIsFlipped(false);
      } else {
        // All cards reviewed
        if (onComplete) {
          onComplete();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return <div className="card-review-loading">Loading cards...</div>;
  }

  if (error) {
    return (
      <div className="card-review-error">
        <p>Error: {error}</p>
        <button onClick={loadDueCards}>Retry</button>
      </div>
    );
  }

  if (dueCards.length === 0) {
    return (
      <div className="card-review-complete">
        <h2>All done!</h2>
        <p>No cards are due for review right now.</p>
        <p>Come back later to continue your learning journey.</p>
      </div>
    );
  }

  const currentCard = dueCards[currentIndex];
  const progress = ((currentIndex + 1) / dueCards.length) * 100;

  return (
    <div className="card-review-container">
      <div className="card-review-header">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <p className="progress-text">
          Card {currentIndex + 1} of {dueCards.length}
        </p>
      </div>

      <div className="card-container">
        <div className={`flashcard ${isFlipped ? 'flipped' : ''}`} onClick={handleFlip}>
          <div className="flashcard-inner">
            <div className="flashcard-front">
              <div className="card-label">Question</div>
              <div className="card-content">{currentCard.card.front}</div>
              <div className="card-hint">Click to reveal answer</div>
            </div>
            <div className="flashcard-back">
              <div className="card-label">Answer</div>
              <div className="card-content">{currentCard.card.back}</div>
            </div>
          </div>
        </div>
      </div>

      {isFlipped && (
        <div className="rating-buttons">
          <p className="rating-prompt">How well did you know this?</p>
          <div className="rating-grid">
            <button
              className="rating-btn rating-again"
              onClick={() => handleRating(0)}
              disabled={reviewing}
            >
              <span className="rating-label">Again</span>
              <span className="rating-description">Complete blackout</span>
            </button>
            <button
              className="rating-btn rating-hard"
              onClick={() => handleRating(2)}
              disabled={reviewing}
            >
              <span className="rating-label">Hard</span>
              <span className="rating-description">Difficult to recall</span>
            </button>
            <button
              className="rating-btn rating-good"
              onClick={() => handleRating(3)}
              disabled={reviewing}
            >
              <span className="rating-label">Good</span>
              <span className="rating-description">Recalled with effort</span>
            </button>
            <button
              className="rating-btn rating-easy"
              onClick={() => handleRating(4)}
              disabled={reviewing}
            >
              <span className="rating-label">Easy</span>
              <span className="rating-description">Perfect recall</span>
            </button>
          </div>
        </div>
      )}

      {currentCard.review.repetitions > 0 && (
        <div className="card-stats">
          <span>Streak: {currentCard.review.streak}</span>
          <span>Reviews: {currentCard.review.total_reviews}</span>
          <span>Interval: {currentCard.review.interval_days} days</span>
        </div>
      )}
    </div>
  );
}
