-- Constraints and indices for study planner database

-- NOTE: user_id in study_plans references users.id in users.db (cross-database)
-- Cannot be enforced as FK in separate SQLite files

-- Add check constraint for user_id validity
ALTER TABLE study_plans ADD CONSTRAINT chk_plan_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

-- Add check constraints for plan validity
ALTER TABLE study_plans ADD CONSTRAINT chk_exam_after_start
    CHECK (exam_date > start_date);

ALTER TABLE study_plans ADD CONSTRAINT chk_daily_minutes_positive
    CHECK (daily_minutes > 0 AND daily_minutes <= 1440); -- Max 24 hours

-- Add check constraints for task validity
ALTER TABLE study_plan_tasks ADD CONSTRAINT chk_task_minutes_positive
    CHECK (minutes > 0 AND minutes <= 1440);

ALTER TABLE study_plan_tasks ADD CONSTRAINT chk_task_subject_not_empty
    CHECK (length(trim(subject)) > 0);

-- Add index for finding tasks by date
CREATE INDEX IF NOT EXISTS idx_tasks_plan_date
    ON study_plan_tasks(plan_id, task_date);

-- Add index for user's plans
CREATE INDEX IF NOT EXISTS idx_plans_user_created
    ON study_plans(user_id, created_at DESC);

-- Note: FK from study_plan_tasks → study_plans already enforced by SQLModel
