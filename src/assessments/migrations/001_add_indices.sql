-- Assessments database indices for performance optimization

-- Index for finding user's assessment history, sorted by time
-- Supports queries like: "show recent assessments for user X"
CREATE INDEX IF NOT EXISTS idx_assess_user_time
    ON assessments(candidate_id, created_at DESC);

-- Index for fast lookup by assessment ID
-- Primary key already provides this, but explicit index for clarity
CREATE INDEX IF NOT EXISTS idx_assess_id
    ON assessments(assessment_id);

-- Index for filtering assessments by status
-- Supports queries like: "get all in-progress assessments for user X"
CREATE INDEX IF NOT EXISTS idx_assess_user_status
    ON assessments(candidate_id, status, created_at DESC);

-- Index for finding assessments by subject/system
-- Supports queries like: "get all Cardiology assessments for user X"
CREATE INDEX IF NOT EXISTS idx_assess_subject
    ON assessments(candidate_id, subject);

CREATE INDEX IF NOT EXISTS idx_assess_system
    ON assessments(candidate_id, system);

-- Index for finding assessments that need to expire
-- Supports scheduled jobs: "find all assessments past expiration time"
CREATE INDEX IF NOT EXISTS idx_assess_expires
    ON assessments(expires_at)
    WHERE status = 'in-progress' AND expires_at IS NOT NULL;

-- Index for performance analytics
-- Supports queries analyzing score distributions
CREATE INDEX IF NOT EXISTS idx_assess_performance
    ON assessments(candidate_id, percentage, submitted_at DESC)
    WHERE status = 'completed';
