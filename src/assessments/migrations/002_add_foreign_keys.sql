-- Foreign key constraints for assessments database

-- NOTE: candidate_id is a string field that logically references users.id
-- but is stored as a string identifier rather than integer FK
-- This is by design for flexibility but limits referential integrity

-- Add check constraints for data validity
ALTER TABLE assessments ADD CONSTRAINT chk_status_valid
    CHECK (status IN ('created', 'ready', 'in-progress', 'completed', 'expired'));

ALTER TABLE assessments ADD CONSTRAINT chk_time_limit_positive
    CHECK (time_limit_minutes > 0);

ALTER TABLE assessments ADD CONSTRAINT chk_scores_non_negative
    CHECK (
        total_questions >= 0 AND
        correct >= 0 AND
        incorrect >= 0 AND
        omitted >= 0 AND
        percentage >= 0.0 AND percentage <= 100.0
    );

ALTER TABLE assessments ADD CONSTRAINT chk_scores_sum
    CHECK (correct + incorrect + omitted <= total_questions);

-- Add check constraint for timestamps logical ordering
ALTER TABLE assessments ADD CONSTRAINT chk_timestamps_order
    CHECK (
        (started_at IS NULL OR started_at >= created_at) AND
        (submitted_at IS NULL OR started_at IS NULL OR submitted_at >= started_at) AND
        (expires_at IS NULL OR started_at IS NULL OR expires_at >= started_at)
    );

ALTER TABLE assessments ADD CONSTRAINT chk_duration_non_negative
    CHECK (duration_seconds IS NULL OR duration_seconds >= 0);
