import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as flashcardApi from '../api/flashcards';
import '../styles/flashcards.css';

export function DeckForm() {
  const navigate = useNavigate();
  const { deckId } = useParams<{ deckId: string }>();
  const { token } = useAuth();
  const isEditing = !!deckId;

  const [formData, setFormData] = useState({
    name: '',
    deck_type: 'ready' as 'ready' | 'smart',
    category: '',
    description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditing && deckId) {
      loadDeck(parseInt(deckId));
    }
  }, [deckId]);

  const loadDeck = async (id: number) => {
    try {
      setLoading(true);
      const deck = await flashcardApi.getDeck(id, token || undefined);
      setFormData({
        name: deck.name,
        deck_type: deck.deck_type,
        category: deck.category || '',
        description: deck.description || '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deck');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('You must be logged in to create or edit decks');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (isEditing && deckId) {
        await flashcardApi.updateDeck(
          parseInt(deckId),
          {
            name: formData.name,
            category: formData.category || undefined,
            description: formData.description || undefined,
          },
          token
        );
      } else {
        const newDeck = await flashcardApi.createDeck(
          {
            name: formData.name,
            deck_type: formData.deck_type,
            category: formData.category || undefined,
            description: formData.description || undefined,
          },
          token
        );
        // Navigate to the new deck's management page
        navigate(`/flashcards/deck/${newDeck.id}`);
        return;
      }

      navigate('/flashcards');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save deck');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/flashcards');
  };

  return (
    <div className="deck-form-container">
      <h1>{isEditing ? 'Edit Deck' : 'Create New Deck'}</h1>

      <form onSubmit={handleSubmit} className="deck-form">
        {error && <div className="form-error">{error}</div>}

        <div className="form-group">
          <label htmlFor="name">Deck Name *</label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="e.g., Anatomy Essentials"
          />
        </div>

        {!isEditing && (
          <div className="form-group">
            <label htmlFor="deck_type">Deck Type *</label>
            <select
              id="deck_type"
              value={formData.deck_type}
              onChange={(e) =>
                setFormData({ ...formData, deck_type: e.target.value as 'ready' | 'smart' })
              }
            >
              <option value="ready">ReadyDeck (Pre-made cards)</option>
              <option value="smart">SmartCard (From QBank questions)</option>
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="category">Category</label>
          <input
            type="text"
            id="category"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            placeholder="e.g., Cardiology, Pharmacology"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={4}
            placeholder="Brief description of what this deck covers..."
          />
        </div>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={handleCancel}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Deck'}
          </button>
        </div>
      </form>
    </div>
  );
}
