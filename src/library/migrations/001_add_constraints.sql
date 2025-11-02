-- Constraints and indices for library database

-- NOTE: user_id in notebook_entries references users.id in users.db (cross-database)
-- Cannot be enforced as FK in separate SQLite files

-- Add check constraint for user_id validity
ALTER TABLE notebook_entries ADD CONSTRAINT chk_note_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

-- Add indices for better query performance
CREATE INDEX IF NOT EXISTS idx_articles_bookmarked
    ON articles(bookmarked)
    WHERE bookmarked = 1;

CREATE INDEX IF NOT EXISTS idx_notes_bookmarked
    ON notebook_entries(bookmarked)
    WHERE bookmarked = 1;

CREATE INDEX IF NOT EXISTS idx_notes_user_created
    ON notebook_entries(user_id, created_at DESC);

-- Articles should have meaningful content
ALTER TABLE articles ADD CONSTRAINT chk_article_title_not_empty
    CHECK (length(trim(title)) > 0);

ALTER TABLE articles ADD CONSTRAINT chk_article_body_not_empty
    CHECK (length(trim(body)) > 0);

-- Notebook entries should have meaningful content
ALTER TABLE notebook_entries ADD CONSTRAINT chk_note_title_not_empty
    CHECK (length(trim(title)) > 0);

ALTER TABLE notebook_entries ADD CONSTRAINT chk_note_body_not_empty
    CHECK (length(trim(body)) > 0);
