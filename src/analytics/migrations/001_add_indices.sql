-- Analytics database indices for performance optimization
-- These indices accelerate common query patterns for user analytics

-- Index for filtering question attempts by user and ordering by time
-- Supports queries like: "get all attempts for user X, ordered by time"
CREATE INDEX IF NOT EXISTS idx_attempts_user_time
    ON question_attempts(user_id, attempted_at DESC);

-- Index for joining question attempts with assessments
-- Supports queries like: "get all attempts for assessment Y"
CREATE INDEX IF NOT EXISTS idx_attempts_assessment
    ON question_attempts(assessment_id);

-- Index for analyzing individual question performance
-- Supports queries like: "get all attempts for question Z"
CREATE INDEX IF NOT EXISTS idx_attempts_question
    ON question_attempts(question_id);

-- Index for subject-based filtering and analytics
-- Supports queries like: "get all attempts for subject 'Cardiology'"
CREATE INDEX IF NOT EXISTS idx_attempts_subject
    ON question_attempts(subject);

-- Index for system-based filtering
-- Supports queries like: "get all attempts for system 'Cardiovascular'"
CREATE INDEX IF NOT EXISTS idx_attempts_system
    ON question_attempts(system);

-- Composite index for common analytics queries
-- Supports: "get user's attempts by difficulty level, sorted by time"
CREATE INDEX IF NOT EXISTS idx_attempts_user_difficulty_time
    ON question_attempts(user_id, difficulty, attempted_at DESC);
