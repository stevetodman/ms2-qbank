import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as flashcardApi from '../api/flashcards';
import '../styles/flashcards.css';

export function DeckManager() {
  const navigate = useNavigate();
  const { deckId } = useParams<{ deckId: string }>();
  const { token } = useAuth();

  const [deck, setDeck] = useState<flashcardApi.Deck | null>(null);
  const [cards, setCards] = useState<flashcardApi.Flashcard[]>([]);
  const [stats, setStats] = useState<flashcardApi.DeckStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCardForm, setShowCardForm] = useState(false);
  const [editingCard, setEditingCard] = useState<flashcardApi.Flashcard | null>(null);
  const [cardFormData, setCardFormData] = useState({ front: '', back: '' });

  useEffect(() => {
    if (deckId) {
      loadDeckData(parseInt(deckId));
    }
  }, [deckId, token]);

  const loadDeckData = async (id: number) => {
    try {
      setLoading(true);
      setError(null);

      const [deckData, cardsData, statsData] = await Promise.all([
        flashcardApi.getDeck(id, token || undefined),
        flashcardApi.listCardsInDeck(id, token || undefined),
        flashcardApi.getDeckStats(id, token || undefined),
      ]);

      setDeck(deckData);
      setCards(cardsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deck');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCard = () => {
    setEditingCard(null);
    setCardFormData({ front: '', back: '' });
    setShowCardForm(true);
  };

  const handleEditCard = (card: flashcardApi.Flashcard) => {
    setEditingCard(card);
    setCardFormData({ front: card.front, back: card.back });
    setShowCardForm(true);
  };

  const handleSaveCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !deckId) return;

    try {
      if (editingCard) {
        await flashcardApi.updateCard(editingCard.id, cardFormData, token);
      } else {
        await flashcardApi.createCard(
          {
            deck_id: parseInt(deckId),
            front: cardFormData.front,
            back: cardFormData.back,
          },
          token
        );
      }

      setShowCardForm(false);
      setCardFormData({ front: '', back: '' });
      setEditingCard(null);
      loadDeckData(parseInt(deckId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save card');
    }
  };

  const handleDeleteCard = async (cardId: number) => {
    if (!token || !deckId) return;
    if (!confirm('Are you sure you want to delete this card?')) return;

    try {
      await flashcardApi.deleteCard(cardId, token);
      loadDeckData(parseInt(deckId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete card');
    }
  };

  const handleDeleteDeck = async () => {
    if (!token || !deckId) return;
    if (!confirm('Are you sure you want to delete this entire deck? This cannot be undone.'))
      return;

    try {
      await flashcardApi.deleteDeck(parseInt(deckId), token);
      navigate('/flashcards');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete deck');
    }
  };

  const handleStudy = () => {
    if (deckId) {
      navigate(`/flashcards/study/${deckId}`);
    }
  };

  if (loading) {
    return <div className="loading-state">Loading deck...</div>;
  }

  if (error || !deck) {
    return (
      <div className="error-state">
        <p>Error: {error || 'Deck not found'}</p>
        <button onClick={() => navigate('/flashcards')}>Back to Decks</button>
      </div>
    );
  }

  return (
    <div className="deck-manager">
      <div className="deck-manager-header">
        <div>
          <h1>{deck.name}</h1>
          {deck.category && <span className="deck-category">{deck.category}</span>}
          {deck.description && <p className="deck-description">{deck.description}</p>}
        </div>
        <div className="header-actions">
          {stats && stats.cards_due_today > 0 && (
            <button className="btn-primary" onClick={handleStudy}>
              Study Now ({stats.cards_due_today})
            </button>
          )}
          <button className="btn-secondary" onClick={() => navigate('/flashcards')}>
            Back to Decks
          </button>
        </div>
      </div>

      {stats && (
        <div className="deck-stats-summary">
          <div className="stat-card">
            <span className="stat-value">{stats.total_cards}</span>
            <span className="stat-label">Total Cards</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.cards_due_today}</span>
            <span className="stat-label">Due Today</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.new_cards}</span>
            <span className="stat-label">New</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.learning_cards}</span>
            <span className="stat-label">Learning</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.mature_cards}</span>
            <span className="stat-label">Mature</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">
              {stats.accuracy_percentage !== undefined
                ? `${Math.round(stats.accuracy_percentage)}%`
                : '-'}
            </span>
            <span className="stat-label">Accuracy</span>
          </div>
        </div>
      )}

      <div className="cards-section">
        <div className="cards-section-header">
          <h2>Cards ({cards.length})</h2>
          <button className="btn-primary" onClick={handleAddCard}>
            + Add Card
          </button>
        </div>

        {showCardForm && (
          <div className="card-form-modal">
            <div className="card-form-content">
              <h3>{editingCard ? 'Edit Card' : 'Add New Card'}</h3>
              <form onSubmit={handleSaveCard}>
                <div className="form-group">
                  <label htmlFor="front">Front (Question) *</label>
                  <textarea
                    id="front"
                    value={cardFormData.front}
                    onChange={(e) => setCardFormData({ ...cardFormData, front: e.target.value })}
                    required
                    rows={4}
                    placeholder="Enter the question or prompt..."
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="back">Back (Answer) *</label>
                  <textarea
                    id="back"
                    value={cardFormData.back}
                    onChange={(e) => setCardFormData({ ...cardFormData, back: e.target.value })}
                    required
                    rows={4}
                    placeholder="Enter the answer..."
                  />
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShowCardForm(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    {editingCard ? 'Save Changes' : 'Add Card'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {cards.length === 0 ? (
          <div className="empty-state">
            <p>No cards in this deck yet.</p>
            <button className="btn-primary" onClick={handleAddCard}>
              Add Your First Card
            </button>
          </div>
        ) : (
          <div className="cards-list">
            {cards.map((card) => (
              <div key={card.id} className="card-item">
                <div className="card-item-content">
                  <div className="card-item-side">
                    <span className="card-side-label">Q:</span>
                    <p>{card.front}</p>
                  </div>
                  <div className="card-item-side">
                    <span className="card-side-label">A:</span>
                    <p>{card.back}</p>
                  </div>
                </div>
                <div className="card-item-actions">
                  <button className="btn-text" onClick={() => handleEditCard(card)}>
                    Edit
                  </button>
                  <button
                    className="btn-text btn-danger"
                    onClick={() => handleDeleteCard(card.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="danger-zone">
        <h3>Danger Zone</h3>
        <p>Once you delete a deck, there is no going back. Please be certain.</p>
        <button className="btn-danger" onClick={handleDeleteDeck}>
          Delete This Deck
        </button>
      </div>
    </div>
  );
}
