-- Foreign key constraints for analytics database
-- NOTE: user_id references users.id in users.db (cross-database, cannot enforce in SQLite)
-- NOTE: assessment_id references assessments.assessment_id in assessments.db (cross-database)

-- Since we're using separate SQLite databases, we cannot enforce cross-database FKs
-- However, we document the logical relationships here for when/if databases are unified

-- The following would be the constraints if using a unified database:
-- ALTER TABLE question_attempts ADD CONSTRAINT fk_attempts_user
--   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
--
-- ALTER TABLE question_attempts ADD CONSTRAINT fk_attempts_assessment
--   FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE SET NULL;

-- For now, we ensure data integrity at the application level
-- and add comments to the schema documentation

-- Add check constraint to ensure user_id is positive when not null
ALTER TABLE question_attempts ADD CONSTRAINT chk_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

-- Add check constraint for attempted_at is not in the future
-- (allowing 5 minute clock skew tolerance)
-- Note: Using datetime() for comparison
