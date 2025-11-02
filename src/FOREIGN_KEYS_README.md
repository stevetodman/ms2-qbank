# Foreign Key Constraints - Implementation Notes

## Overview

This document explains the foreign key constraint strategy for the MS2 QBank microservices architecture.

## Architecture Context

The application uses a **microservices architecture** with **separate SQLite databases** per service:

```
data/
├── analytics.db      # User performance analytics
├── assessments.db    # Self-assessments
├── flashcards.db     # Flashcard decks and reviews
├── library.db        # Articles and notebook entries
├── planner.db        # Study plans
├── users.db          # User accounts and authentication
└── videos.db         # Video library and progress
```

## Foreign Key Limitation

**SQLite cannot enforce foreign key constraints across separate database files.**

### Affected Relationships

These logical foreign keys exist but **cannot be enforced at the database level**:

| Service | Column | References | Strategy |
|---------|--------|------------|----------|
| analytics | `question_attempts.user_id` | `users.id` | Application-level integrity |
| analytics | `question_attempts.assessment_id` | `assessments.assessment_id` | Application-level integrity |
| videos | `video_progress.user_id` | `users.id` | Application-level integrity |
| videos | `video_bookmarks.user_id` | `users.id` | Application-level integrity |
| videos | `playlists.user_id` | `users.id` | Application-level integrity |
| flashcards | `decks.user_id` | `users.id` | Application-level integrity |
| flashcards | `card_reviews.user_id` | `users.id` | Application-level integrity |
| assessments | `assessments.candidate_id` | `users.id` | Application-level integrity + string ID |
| library | `notebook_entries.user_id` | `users.id` | Application-level integrity |
| planner | `study_plans.user_id` | `users.id` | Application-level integrity |

## What IS Enforced

Foreign keys **within the same database** are properly enforced:

### videos.db
- ✅ `playlist_videos.playlist_id` → `playlists.id` (CASCADE)
- ✅ `playlist_videos.video_id` → `videos.id` (CASCADE)
- ✅ `video_progress.video_id` → `videos.id` (CASCADE)
- ✅ `video_bookmarks.video_id` → `videos.id` (CASCADE)

### flashcards.db
- ✅ `flashcards.deck_id` → `decks.id` (CASCADE)
- ✅ `card_reviews.card_id` → `flashcards.id` (CASCADE)

### planner.db
- ✅ `study_plan_tasks.plan_id` → `study_plans.plan_id` (CASCADE)

### users.db
- ✅ `refresh_tokens.user_id` → `users.id` (CASCADE)

## Migration Strategy

Each service has migration files in `src/<service>/migrations/`:

1. **`001_add_indices.sql`** - Performance optimization indices
2. **`002_add_foreign_keys.sql`** or **`001_add_constraints.sql`** - Constraints and documentation

### Check Constraints

While we can't enforce cross-database FKs, we've added **check constraints** for data validity:

```sql
-- Ensure user_id is positive when present
ALTER TABLE question_attempts ADD CONSTRAINT chk_user_id_positive
    CHECK (user_id IS NULL OR user_id > 0);

-- Ensure logical timestamp ordering
ALTER TABLE assessments ADD CONSTRAINT chk_timestamps_order
    CHECK (submitted_at IS NULL OR submitted_at >= started_at);

-- Ensure scores are valid
ALTER TABLE assessments ADD CONSTRAINT chk_scores_sum
    CHECK (correct + incorrect + omitted <= total_questions);
```

## Application-Level Integrity

Services maintain referential integrity through:

1. **Authentication middleware** - Validates user_id from JWT tokens
2. **Existence checks** - Services verify referenced entities exist before creating relationships
3. **Soft deletes** - Some services use soft deletion to preserve analytics
4. **Orphan cleanup jobs** - Periodic background tasks clean up orphaned records

## Future: Unified Database

If/when migrating to a unified PostgreSQL database, all foreign keys can be properly enforced:

```sql
-- Future: When using unified PostgreSQL database
ALTER TABLE question_attempts ADD CONSTRAINT fk_attempts_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE video_progress ADD CONSTRAINT fk_progress_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## Testing

Integration tests validate cross-service data integrity:

- `tests/test_user_auth.py` - User lifecycle and cascading deletes
- `tests/test_integration_services.py` - Cross-service data consistency (TODO)

## Recommendations

For production deployments:

1. **Use PostgreSQL** - Enables true foreign key enforcement across all tables
2. **Implement orphan cleanup** - Scheduled jobs to detect and handle orphaned records
3. **Add monitoring** - Alert on orphaned records or referential integrity violations
4. **Document relationships** - Keep this file updated as schema evolves

## References

- SQLite Foreign Key Support: https://www.sqlite.org/foreignkeys.html
- SQLite Attach Database: https://www.sqlite.org/lang_attach.html (partial workaround)
- Migration files: `src/*/migrations/*.sql`
