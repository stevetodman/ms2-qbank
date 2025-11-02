-- Flashcards database indices for performance optimization

-- Unique index to ensure one review state per user-card pair
-- Also speeds up lookups: "get review state for user X on card Y"
CREATE UNIQUE INDEX IF NOT EXISTS ux_reviews_user_card
    ON card_reviews(user_id, card_id);

-- Index for finding cards due for review
-- Critical for the spaced repetition scheduler
-- Supports queries like: "get all cards due today or earlier"
CREATE INDEX IF NOT EXISTS idx_reviews_due
    ON card_reviews(next_review_date);

-- Composite index for finding due cards for a specific user
-- Supports queries like: "get user X's cards due for review"
CREATE INDEX IF NOT EXISTS idx_reviews_user_due
    ON card_reviews(user_id, next_review_date);

-- Index for finding all cards in a deck
-- Supports queries like: "get all cards in deck Y"
CREATE INDEX IF NOT EXISTS idx_cards_deck
    ON flashcards(deck_id, created_at);

-- Index for finding active decks for a user
-- Supports queries like: "show my active decks"
CREATE INDEX IF NOT EXISTS idx_decks_user_active
    ON decks(user_id, is_active, created_at DESC);

-- Index for finding cards by review status (new/learning/mature)
-- Based on repetitions count
CREATE INDEX IF NOT EXISTS idx_reviews_repetitions
    ON card_reviews(card_id, repetitions);

-- Index for performance analytics on reviews
-- Supports queries analyzing streak and quality patterns
CREATE INDEX IF NOT EXISTS idx_reviews_quality_streak
    ON card_reviews(user_id, last_quality, streak);
