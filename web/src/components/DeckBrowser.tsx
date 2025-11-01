import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as flashcardApi from '../api/flashcards';
import '../styles/flashcards.css';

type DeckType = 'ready' | 'smart';

interface DeckWithStats {
  deck: flashcardApi.Deck;
  stats?: flashcardApi.DeckStats;
}

export function DeckBrowser() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<DeckType>('ready');
  const [decks, setDecks] = useState<DeckWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDecks();
  }, [activeTab, token]);

  const loadDecks = async () => {
    try {
      setLoading(true);
      setError(null);
      const deckList = await flashcardApi.listDecks(activeTab, token || undefined);

      // Load stats for each deck
      const decksWithStats = await Promise.all(
        deckList.map(async (deck) => {
          try {
            const stats = await flashcardApi.getDeckStats(deck.id, token || undefined);
            return { deck, stats };
          } catch {
            return { deck };
          }
        })
      );

      setDecks(decksWithStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decks');
    } finally {
      setLoading(false);
    }
  };

  const handleStudyDeck = (deckId: number) => {
    navigate(`/flashcards/study/${deckId}`);
  };

  const handleManageDeck = (deckId: number) => {
    navigate(`/flashcards/deck/${deckId}`);
  };

  const handleCreateDeck = () => {
    navigate('/flashcards/create');
  };

  return (
    <div className="deck-browser">
      <div className="deck-browser-header">
        <h1>Flashcards</h1>
        <button className="btn-primary" onClick={handleCreateDeck}>
          + Create New Deck
        </button>
      </div>

      <div className="deck-tabs">
        <button
          className={`tab-btn ${activeTab === 'ready' ? 'active' : ''}`}
          onClick={() => setActiveTab('ready')}
        >
          ReadyDecks
          <span className="tab-description">Pre-made by experts</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'smart' ? 'active' : ''}`}
          onClick={() => setActiveTab('smart')}
        >
          SmartCards
          <span className="tab-description">Created from your QBank</span>
        </button>
      </div>

      <div className="deck-content">
        {loading && <div className="loading-state">Loading decks...</div>}

        {error && (
          <div className="error-state">
            <p>Error: {error}</p>
            <button onClick={loadDecks}>Retry</button>
          </div>
        )}

        {!loading && !error && decks.length === 0 && (
          <div className="empty-state">
            <h2>No {activeTab === 'ready' ? 'ReadyDecks' : 'SmartCards'} yet</h2>
            {activeTab === 'ready' ? (
              <p>Create your first ReadyDeck to get started with flashcard learning.</p>
            ) : (
              <p>
                SmartCards are created from QBank questions you've reviewed. Start practicing
                questions to build your personalized deck!
              </p>
            )}
            {activeTab === 'ready' && (
              <button className="btn-primary" onClick={handleCreateDeck}>
                Create Your First Deck
              </button>
            )}
          </div>
        )}

        {!loading && !error && decks.length > 0 && (
          <div className="deck-grid">
            {decks.map(({ deck, stats }) => (
              <div key={deck.id} className="deck-card">
                <div className="deck-card-header">
                  <h3>{deck.name}</h3>
                  {deck.category && <span className="deck-category">{deck.category}</span>}
                </div>

                {deck.description && <p className="deck-description">{deck.description}</p>}

                {stats && (
                  <div className="deck-stats-grid">
                    <div className="stat-item">
                      <span className="stat-value">{stats.total_cards}</span>
                      <span className="stat-label">Total Cards</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{stats.cards_due_today}</span>
                      <span className="stat-label">Due Today</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{stats.new_cards}</span>
                      <span className="stat-label">New</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">
                        {stats.accuracy_percentage !== undefined
                          ? `${Math.round(stats.accuracy_percentage)}%`
                          : '-'}
                      </span>
                      <span className="stat-label">Accuracy</span>
                    </div>
                  </div>
                )}

                <div className="deck-card-actions">
                  {stats && stats.cards_due_today > 0 ? (
                    <button
                      className="btn-primary btn-study"
                      onClick={() => handleStudyDeck(deck.id)}
                    >
                      Study Now ({stats.cards_due_today})
                    </button>
                  ) : (
                    <button
                      className="btn-secondary btn-study"
                      onClick={() => handleStudyDeck(deck.id)}
                      disabled={!stats || stats.total_cards === 0}
                    >
                      {stats && stats.total_cards === 0 ? 'No Cards' : 'Up to Date'}
                    </button>
                  )}
                  <button className="btn-text" onClick={() => handleManageDeck(deck.id)}>
                    Manage
                  </button>
                </div>

                <div className="deck-card-footer">
                  <span className="deck-type-badge">{deck.deck_type}</span>
                  <span className="deck-date">
                    Updated {new Date(deck.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
