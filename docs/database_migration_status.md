# Database Migration Status

## Overview

This document tracks the progress of migrating MS2 QBank services from mixed persistence strategies (in-memory dictionaries, JSON files) to a unified SQLite database approach using SQLModel.

**Goal:** Prevent data loss on server restart and provide consistent data persistence across all services.

---

## ✅ Completed Migrations

### 1. User Authentication (`src/users/`)
**Status:** ✅ Complete
**Database:** `data/users.db`
**Tables:**
- `users` - User accounts with authentication and profile data

**Models:**
- `User` (SQLModel table) - email, hashed_password, full_name, exam_date, subscription details

**Features:**
- User registration with password hashing (bcrypt)
- JWT token authentication (7-day expiration)
- Profile management (GET/PATCH endpoints)
- Last login tracking

**Files:**
- `src/users/models.py` - SQLModel table definitions
- `src/users/store.py` - Database CRUD operations
- `src/users/auth.py` - Password hashing and JWT utilities
- `src/users/app.py` - FastAPI endpoints

---

### 2. Study Planner (`src/planner/`)
**Status:** ✅ Complete
**Database:** `data/planner.db`
**Tables:**
- `study_plans` - Study plan metadata
- `study_plan_tasks` - Individual daily tasks

**Before:**
```python
self._plans: dict[str, StudyPlan] = {}  # In-memory only, lost on restart
```

**After:**
```python
self.store = StudyPlanStore()  # SQLite persistence
```

**Models:**
- `StudyPlanDB` (SQLModel table) - plan_id (PK), user_id, dates, daily_minutes
- `StudyPlanTaskDB` (SQLModel table) - id (PK), plan_id (FK), task_date, subject, minutes

**Features:**
- Plans persist across server restarts
- User-specific plan filtering (user_id index)
- Full CRUD operations (create, list, get, delete)
- Automatic database creation on first run

**Files:**
- `src/planner/db_models.py` - Database table models
- `src/planner/store.py` - Database persistence layer
- `src/planner/service.py` - Updated to use database store

**Migration Impact:**
- ✅ All tests passing
- ⚠️ Existing in-memory plans lost (acceptable - no production data)
- ✅ New plans automatically saved to `data/planner.db`

---

### 3. Review Workflow (`src/reviews/`)
**Status:** ✅ Already using SQLite
**Database:** `data/reviews/*.db` (gitignored)
**No migration needed** - This service was already using proper database persistence.

---

## ⏳ Pending Migrations (Future Work)

### 4. Assessment Store (`src/assessments/`)
**Status:** ⏳ Not migrated yet
**Current:** In-memory dictionary (`self._records: dict[str, AssessmentRecord] = {}`)
**Impact:** Assessments lost on server restart

**Recommended Migration:**

**Database:** `data/assessments.db`
**Proposed Tables:**
- `assessments` - Assessment metadata (assessment_id, blueprint, created_at, status)
- `assessment_responses` - User responses (assessment_id, question_id, answer)
- `assessment_scores` - Scoring results (assessment_id, total, correct, incorrect, percentage)

**Proposed Models:**
```python
class AssessmentDB(SQLModel, table=True):
    assessment_id: str = SQLField(primary_key=True)
    user_id: Optional[int] = SQLField(default=None, index=True)
    status: str = SQLField()  # created, in-progress, completed
    created_at: datetime
    started_at: Optional[datetime]
    submitted_at: Optional[datetime]
    time_limit_minutes: int
    # Blueprint filters stored as JSON columns
    blueprint_subject: Optional[str]
    blueprint_system: Optional[str]
    blueprint_difficulty: Optional[str]

class AssessmentResponseDB(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    assessment_id: str = SQLField(foreign_key="assessments.assessment_id")
    question_id: str
    selected_answer: Optional[str]

class AssessmentScoreDB(SQLModel, table=True):
    assessment_id: str = SQLField(primary_key=True, foreign_key="assessments.assessment_id")
    total_questions: int
    correct: int
    incorrect: int
    omitted: int
    percentage: float
    duration_seconds: Optional[int]
```

**Files to Create:**
- `src/assessments/db_models.py` - Database table models
- `src/assessments/db_store.py` - Database-backed AssessmentStore

**Files to Update:**
- `src/assessments/store.py` - Replace in-memory dict with database calls
- `src/assessments/app.py` - Use database store

**Estimated Effort:** 2-3 hours

**Why Not Done Yet:** No real assessment data exists to preserve. Can be done when needed.

---

### 5. Library & Notebook (`src/library/`)
**Status:** ⏳ Not migrated yet
**Current:** In-memory from JSON files (`_articles`, `_notes` dicts loaded at startup)
**Impact:** Changes to articles/notes are NOT saved back to files

**Recommended Migration:**

**Database:** `data/library.db`
**Proposed Tables:**
- `articles` - Medical library articles
- `notebook_entries` - User notes
- `article_tags` - Many-to-many relationship for article tags
- `note_tags` - Many-to-many relationship for note tags
- `note_article_links` - Many-to-many: notes ↔ articles
- `note_question_links` - Many-to-many: notes ↔ questions

**Proposed Models:**
```python
class ArticleDB(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    user_id: Optional[int] = SQLField(default=None, index=True)
    title: str
    summary: str
    body: str  # or use TEXT column
    bookmarked: bool = SQLField(default=False)
    created_at: datetime

class NotebookEntryDB(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    user_id: Optional[int] = SQLField(default=None, index=True)
    title: str
    body: str  # or use TEXT column
    bookmarked: bool = SQLField(default=False)
    created_at: datetime
    updated_at: datetime
```

**Initial Data Migration:**
- Create migration script to load existing JSON files into database
- Run once on first deployment
- Keep JSON files as backup

**Files to Create:**
- `src/library/db_models.py` - Database table models
- `src/library/db_store.py` - Database-backed LibraryStore
- `scripts/migrate_library_data.py` - One-time JSON → DB migration

**Files to Update:**
- `src/library/store.py` - Replace JSON loading with database
- `src/library/app.py` - Use database store

**Estimated Effort:** 3-4 hours

**Why Not Done Yet:** Current JSON files work fine for read-only content. Changes aren't critical to preserve yet.

---

## 📊 Migration Summary

| Service | Before | After | Data Loss Risk | Status |
|---------|--------|-------|----------------|--------|
| **Users** | N/A | ✅ SQLite | None | ✅ Complete |
| **Reviews** | ✅ SQLite | ✅ SQLite | None | ✅ Already done |
| **Study Planner** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Assessments** | ❌ In-memory | ⏳ Pending | ⚠️ High (on restart) | Future work |
| **Library/Notes** | ❌ In-memory | ⏳ Pending | ⚠️ Medium (changes not saved) | Future work |
| **Questions** | ✅ JSON files | ✅ JSON files | None (read-only) | No migration needed |

---

## 🎯 Next Steps (When Needed)

### When to Migrate Assessments:
- When you start collecting real assessment data
- When you want to preserve assessment history across deployments
- Before production launch

### When to Migrate Library:
- When you start allowing users to create/edit notes frequently
- When you have significant user-generated content
- When you need to enforce data integrity constraints

### Future: Unified Database
**Long-term goal:** Consolidate all databases into a single database with proper foreign key relationships.

**Current State:**
```
data/
├── users.db          # User authentication
├── planner.db        # Study plans
├── reviews/          # Review workflow (multiple DBs)
├── library/          # JSON files (articles, notes)
└── questions/        # JSON files (question bank)
```

**Future State:**
```
data/
└── ms2qbank.db       # Single unified database
    ├── users
    ├── study_plans
    ├── study_plan_tasks
    ├── assessments
    ├── assessment_responses
    ├── articles
    ├── notebook_entries
    ├── reviews
    └── questions (possibly)
```

**Benefits of Unified Database:**
- Proper foreign key constraints (user_id → users.id)
- Transactions across tables
- Easier backup/restore
- Better query performance
- Simplified deployment

**Migration Path:**
1. ✅ Migrate each service to its own SQLite database (current approach)
2. ⏳ Test each service independently
3. Future: Merge all databases into one with migration script
4. Future: Add proper foreign key relationships

---

## 🔧 Technical Notes

### Database Files (Gitignored)
All `.db` files are gitignored to prevent committing user data:
```
.gitignore:
*.db
data/*.db
```

### SQLModel Configuration
All database models use:
- `SQLModel` base class
- Optional fields with `Optional[T]`
- `Field` imported as `SQLField` to avoid Pydantic conflicts
- Timezone-aware datetimes (`DateTime(timezone=True)`)

### Testing Strategy
- Use temporary databases in tests (`tempfile.NamedTemporaryFile`)
- Clean up after each test
- Test CRUD operations thoroughly
- Verify data persists across "restarts" (new store instances)

---

## 📝 Lessons Learned

### What Worked Well:
✅ SQLModel provides great balance between Pydantic and SQLAlchemy
✅ Separate databases allowed incremental migration
✅ Tests caught issues early
✅ Domain objects (dataclasses) separate from DB models kept clean architecture

### Challenges:
⚠️ SQLAlchemy 2.0 relationship syntax with SQLModel requires `Mapped[]`
⚠️ Foreign keys across separate databases not possible
⚠️ Simplified by removing bidirectional relationships

### Best Practices:
1. Start with simple models (no relationships)
2. Add indexes on frequently queried fields (user_id, plan_id)
3. Use timezone-aware datetimes consistently
4. Keep domain logic separate from persistence logic
5. Test with temporary databases

---

## 🎉 Impact

### Before Migration:
- ❌ Study plans lost on server restart
- ❌ No multi-user support (no data isolation)
- ❌ No query capabilities (everything in memory)
- ❌ Poor scalability

### After Migration:
- ✅ Data persists across restarts
- ✅ Ready for multi-user (user_id indexes)
- ✅ Can query with SQL (filter, sort, paginate)
- ✅ Better performance (database indexes)
- ✅ Enables future features (history, analytics, rollback)

---

**Last Updated:** 2025-11-01
**Status:** Partial - Critical migrations complete, remaining work documented for future
