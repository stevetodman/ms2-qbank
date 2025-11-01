import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import * as flashcardApi from '../api/flashcards';
import type { QuestionPayload } from '../types/practice';
import { questionToFlashcard, getFlashcardPreview } from '../utils/flashcardConverter';
import '../styles/flashcards.css';

interface CreateSmartCardModalProps {
  question: QuestionPayload;
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateSmartCardModal({ question, onClose, onSuccess }: CreateSmartCardModalProps) {
  const { token } = useAuth();
  const [smartDecks, setSmartDecks] = useState<flashcardApi.Deck[]>([]);
  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [newDeckName, setNewDeckName] = useState('');
  const [creatingNew, setCreatingNew] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const preview = getFlashcardPreview(question);

  useEffect(() => {
    loadSmartDecks();
  }, [token]);

  const loadSmartDecks = async () => {
    try {
      setLoading(true);
      const decks = await flashcardApi.listDecks('smart', token || undefined);
      setSmartDecks(decks);

      // Auto-select the first deck if available
      if (decks.length > 0) {
        setSelectedDeckId(decks[0].id);
      } else {
        // No decks exist, suggest creating one
        setCreatingNew(true);
        setNewDeckName(
          question.metadata?.subject
            ? `${question.metadata.subject} SmartCards`
            : 'My SmartCards'
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCard = async () => {
    if (!token) {
      setError('You must be logged in to create flashcards');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      let deckId = selectedDeckId;

      // Create new deck if needed
      if (creatingNew) {
        if (!newDeckName.trim()) {
          setError('Please enter a deck name');
          return;
        }

        const newDeck = await flashcardApi.createDeck(
          {
            name: newDeckName,
            deck_type: 'smart',
            category: question.metadata?.subject,
            description: 'Created from QBank questions',
          },
          token
        );
        deckId = newDeck.id;
      }

      if (!deckId) {
        setError('Please select a deck');
        return;
      }

      // Create the flashcard
      const cardData = questionToFlashcard(question, deckId);
      await flashcardApi.createCard(cardData, token);

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create flashcard');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card-form-modal" onClick={onClose}>
      <div className="card-form-content smartcard-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Create SmartCard</h3>

        <div className="form-group">
          <label>Preview</label>
          <div className="flashcard-preview">
            <div className="preview-side">
              <span className="preview-label">Front (Question)</span>
              <p className="preview-text">{preview.front.substring(0, 150)}...</p>
            </div>
            <div className="preview-side">
              <span className="preview-label">Back (Answer)</span>
              <p className="preview-text">{preview.back.substring(0, 150)}...</p>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">Loading your SmartCard decks...</div>
        ) : (
          <>
            <div className="form-group">
              <label>Select Deck</label>
              {smartDecks.length > 0 && !creatingNew ? (
                <select
                  value={selectedDeckId || ''}
                  onChange={(e) => setSelectedDeckId(parseInt(e.target.value))}
                >
                  {smartDecks.map((deck) => (
                    <option key={deck.id} value={deck.id}>
                      {deck.name}
                      {deck.category ? ` (${deck.category})` : ''}
                    </option>
                  ))}
                </select>
              ) : creatingNew ? (
                <input
                  type="text"
                  value={newDeckName}
                  onChange={(e) => setNewDeckName(e.target.value)}
                  placeholder="Enter deck name"
                  autoFocus
                />
              ) : null}
            </div>

            {smartDecks.length > 0 && !creatingNew && (
              <button
                type="button"
                className="btn-text"
                onClick={() => {
                  setCreatingNew(true);
                  setNewDeckName(
                    question.metadata?.subject
                      ? `${question.metadata.subject} SmartCards`
                      : 'My SmartCards'
                  );
                }}
              >
                + Create New Deck Instead
              </button>
            )}

            {creatingNew && smartDecks.length > 0 && (
              <button
                type="button"
                className="btn-text"
                onClick={() => {
                  setCreatingNew(false);
                  setSelectedDeckId(smartDecks[0].id);
                }}
              >
                ← Use Existing Deck
              </button>
            )}
          </>
        )}

        {error && <div className="form-error">{error}</div>}

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleCreateCard}
            disabled={saving || loading}
          >
            {saving ? 'Creating...' : 'Create SmartCard'}
          </button>
        </div>

        <div className="modal-hint">
          <small>
            This will create a flashcard from this question. You can review it later in the
            Flashcards section.
          </small>
        </div>
      </div>
    </div>
  );
}
