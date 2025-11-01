import { useEffect, useMemo, useState } from 'react';
import {
  fetchDeckDetail,
  listDecks,
  type FlashcardDeckDetail,
  type FlashcardDeckSummary,
  type FlashcardDeckType,
} from '../api/flashcards.ts';

const TAB_DEFINITIONS: { label: string; value: FlashcardDeckType; description: string }[] = [
  {
    label: 'ReadyDecks',
    value: 'ready',
    description: 'Expert-authored, premade decks covering high-yield Step 1 systems and disciplines.',
  },
  {
    label: 'SmartCards',
    value: 'smart',
    description: 'Personal decks you curate from practice sessions, notebook highlights, and custom notes.',
  },
];

interface DeckBuckets {
  ready: FlashcardDeckSummary[];
  smart: FlashcardDeckSummary[];
}

const initialBuckets: DeckBuckets = { ready: [], smart: [] };

export const FlashcardsRoute = () => {
  const [deckType, setDeckType] = useState<FlashcardDeckType>('ready');
  const [deckBuckets, setDeckBuckets] = useState<DeckBuckets>(initialBuckets);
  const [loadingDecks, setLoadingDecks] = useState(false);
  const [deckError, setDeckError] = useState<string | null>(null);

  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [selectedDeck, setSelectedDeck] = useState<FlashcardDeckDetail | null>(null);
  const [loadingDeckDetail, setLoadingDeckDetail] = useState(false);
  const [deckDetailError, setDeckDetailError] = useState<string | null>(null);

  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoadingDecks(true);
    setDeckError(null);
    listDecks()
      .then((decks) => {
        if (cancelled) {
          return;
        }
        const nextBuckets = decks.reduce<DeckBuckets>(
          (acc, deck) => {
            acc[deck.deckType].push(deck);
            return acc;
          },
          { ready: [] as FlashcardDeckSummary[], smart: [] as FlashcardDeckSummary[] },
        );
        setDeckBuckets(nextBuckets);
        setDeckType((current) => {
          if (current === 'ready' && nextBuckets.ready.length === 0 && nextBuckets.smart.length > 0) {
            return 'smart';
          }
          if (current === 'smart' && nextBuckets.smart.length === 0 && nextBuckets.ready.length > 0) {
            return 'ready';
          }
          return current;
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message = error instanceof Error ? error.message : 'Unable to load flashcard decks';
        setDeckError(message);
        setDeckBuckets({ ready: [], smart: [] });
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingDecks(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const decksForType = useMemo(() => deckBuckets[deckType], [deckBuckets, deckType]);

  useEffect(() => {
    if (decksForType.length === 0) {
      setSelectedDeckId(null);
      setSelectedDeck(null);
      return;
    }
    setSelectedDeckId((current) => {
      if (current && decksForType.some((deck) => deck.id === current)) {
        return current;
      }
      return decksForType[0].id;
    });
  }, [decksForType]);

  useEffect(() => {
    if (selectedDeckId === null) {
      setSelectedDeck(null);
      setDeckDetailError(null);
      return;
    }

    let cancelled = false;
    setLoadingDeckDetail(true);
    setDeckDetailError(null);
    fetchDeckDetail(selectedDeckId)
      .then((detail) => {
        if (cancelled) {
          return;
        }
        setSelectedDeck(detail);
        setActiveCardIndex(0);
        setShowAnswer(false);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message = error instanceof Error ? error.message : 'Unable to load deck';
        setDeckDetailError(message);
        setSelectedDeck(null);
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingDeckDetail(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedDeckId]);

  const currentDeck = selectedDeck;
  const cards = currentDeck?.cards ?? [];
  const currentCard = cards[activeCardIndex] ?? null;

  const goToPrevious = () => {
    if (!currentDeck) {
      return;
    }
    setActiveCardIndex((index) => Math.max(index - 1, 0));
    setShowAnswer(false);
  };

  const goToNext = () => {
    if (!currentDeck) {
      return;
    }
    setActiveCardIndex((index) => Math.min(index + 1, currentDeck.cards.length - 1));
    setShowAnswer(false);
  };

  return (
    <main className="stack">
      <section className="card stack">
        <header className="stack">
          <h1>Flashcards Study Studio</h1>
          <p>
            Work through curated ReadyDecks or revisit your SmartCards with an interactive study
            surface that tracks context, tags, and explanations. Flip each card to reveal step-by-step
            answers, and advance at your own pace.
          </p>
        </header>
        <nav className="toolbar" aria-label="Flashcard collections">
          {TAB_DEFINITIONS.map((tab) => {
            const isActive = deckType === tab.value;
            return (
              <button
                key={tab.value}
                type="button"
                className={isActive ? 'primary-button' : 'secondary-button'}
                onClick={() => {
                  setDeckType(tab.value);
                }}
              >
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
        <p className="tab-description">{TAB_DEFINITIONS.find((tab) => tab.value === deckType)?.description}</p>
      </section>

      <section className="card flashcards-layout">
        <div className="deck-list-panel">
          <header className="stack">
            <h2>{deckType === 'ready' ? 'ReadyDecks' : 'SmartCards'}</h2>
            {loadingDecks && <p>Loading decks…</p>}
            {deckError && (
              <p role="alert" className="error">
                {deckError}
              </p>
            )}
          </header>
          {decksForType.length === 0 && !loadingDecks && !deckError && (
            <p className="empty-state">No decks available yet for this category.</p>
          )}
          <ul className="deck-list">
            {decksForType.map((deck) => {
              const isSelected = deck.id === selectedDeckId;
              return (
                <li key={deck.id}>
                  <button
                    type="button"
                    className={isSelected ? 'deck-button selected' : 'deck-button'}
                    onClick={() => {
                      setSelectedDeckId(deck.id);
                    }}
                  >
                    <span className="deck-name">{deck.name}</span>
                    <span className="deck-count">{deck.cardCount} cards</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="study-panel stack">
          {loadingDeckDetail && <p>Loading deck…</p>}
          {deckDetailError && (
            <p role="alert" className="error">
              {deckDetailError}
            </p>
          )}
          {!loadingDeckDetail && !deckDetailError && currentDeck && (
            <div className="stack">
              <header className="stack">
                <div className="toolbar" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div className="stack" style={{ margin: 0 }}>
                    <h2>{currentDeck.name}</h2>
                    {currentDeck.description && <p>{currentDeck.description}</p>}
                  </div>
                  <span className="badge">{currentDeck.cardCount} cards</span>
                </div>
              </header>

              {currentCard ? (
                <div className="stack">
                  <article className="study-card stack" aria-live="polite">
                    <header className="toolbar" style={{ justifyContent: 'space-between' }}>
                      <span className="badge">
                        Card {activeCardIndex + 1} / {currentDeck.cards.length}
                      </span>
                      <div className="toolbar" style={{ margin: 0 }}>
                        <button
                          type="button"
                          onClick={() => {
                            setShowAnswer((prev) => !prev);
                          }}
                        >
                          {showAnswer ? 'Hide answer' : 'Reveal answer'}
                        </button>
                      </div>
                    </header>
                    <div className="card-face">
                      <h3>Prompt</h3>
                      <p>{currentCard.prompt}</p>
                    </div>
                    {showAnswer && (
                      <div className="card-face answer">
                        <h3>Answer</h3>
                        <p>{currentCard.answer}</p>
                        {currentCard.explanation && <p className="explanation">{currentCard.explanation}</p>}
                      </div>
                    )}
                    {currentCard.tags.length > 0 && (
                      <div className="toolbar" style={{ marginTop: '0.75rem' }}>
                        {currentCard.tags.map((tag) => (
                          <span key={tag} className="badge">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </article>
                  <div className="toolbar" style={{ justifyContent: 'space-between' }}>
                    <button type="button" onClick={goToPrevious} disabled={activeCardIndex === 0}>
                      Previous card
                    </button>
                    <button
                      type="button"
                      onClick={goToNext}
                      disabled={activeCardIndex >= currentDeck.cards.length - 1}
                    >
                      Next card
                    </button>
                  </div>
                </div>
              ) : (
                <p className="empty-state">This deck does not contain any cards yet.</p>
              )}
            </div>
          )}
        </div>
      </section>
    </main>
  );
};

export default FlashcardsRoute;
