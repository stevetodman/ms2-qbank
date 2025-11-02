-- Foreign key constraints for flashcards database

-- NOTE: user_id columns reference users.id in users.db (cross-database in SQLite)
-- These cannot be enforced as FKs in separate SQLite files

-- Add check constraints for data validity
ALTER TABLE decks ADD CONSTRAINT chk_deck_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

ALTER TABLE card_reviews ADD CONSTRAINT chk_review_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

-- Add check constraints for spaced repetition values
ALTER TABLE card_reviews ADD CONSTRAINT chk_ease_factor_range
    CHECK (ease_factor >= 1.3 AND ease_factor <= 2.5);

ALTER TABLE card_reviews ADD CONSTRAINT chk_interval_non_negative
    CHECK (interval_days >= 0);

ALTER TABLE card_reviews ADD CONSTRAINT chk_repetitions_non_negative
    CHECK (repetitions >= 0);

-- Add composite unique constraint for card reviews (one review state per user-card pair)
CREATE UNIQUE INDEX IF NOT EXISTS ux_card_reviews_user_card
    ON card_reviews(user_id, card_id);

-- Note: Existing FKs (flashcards → decks, card_reviews → flashcards) are already
-- enforced via SQLModel's foreign_key parameter
