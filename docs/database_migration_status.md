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

### 4. Flashcard System (`src/flashcards/`)
**Status:** ✅ Complete
**Database:** `data/flashcards.db`
**Tables:**
- `decks` - Flashcard decks (user-created and official)
- `cards` - Individual flashcards
- `card_reviews` - User review history for spaced repetition

**Features:**
- SM-2 spaced repetition algorithm
- User-specific review tracking
- Deck statistics and due card management
- Question-to-flashcard conversion
- QBank integration for creating cards from questions

**Files:**
- `src/flashcards/models.py` - Database and API models
- `src/flashcards/store.py` - Database operations with SM-2 algorithm
- `src/flashcards/app.py` - FastAPI endpoints (port 8001)

---

### 5. Video Library (`src/videos/`)
**Status:** ✅ Complete
**Database:** `data/videos.db`
**Tables:**
- `videos` - Video content metadata
- `playlists` - User and official playlists
- `playlist_videos` - Many-to-many playlist/video relationship
- `video_progress` - User progress tracking
- `video_bookmarks` - User-created timestamp bookmarks

**Features:**
- Video catalog with categorization (subject, system, topic)
- Playlist management (user and official)
- Watch progress tracking
- Timestamp bookmarks with notes
- View count analytics
- Integrated authentication for user-specific features

**Files:**
- `src/videos/models.py` - Database and API models
- `src/videos/store.py` - Database operations
- `src/videos/app.py` - FastAPI endpoints (port 8003)

---

### 6. User Performance Analytics (`src/analytics/`)
**Status:** ✅ Complete
**Database:** `data/analytics.db`
**Table:** `question_attempts`

**Model:**
```python
class QuestionAttemptDB(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: Optional[int] = SQLField(index=True)
    question_id: str = SQLField(max_length=255, index=True)
    assessment_id: Optional[str] = SQLField(max_length=255, index=True)

    # Question metadata (denormalized for performance)
    subject: Optional[str] = SQLField(max_length=100, index=True)
    system: Optional[str] = SQLField(max_length=100, index=True)
    difficulty: Optional[str] = SQLField(max_length=50)

    # Attempt details
    answer_given: Optional[str]
    correct_answer: str
    is_correct: bool = SQLField(index=True)
    time_seconds: Optional[int]
    mode: str = SQLField(default="practice")
    attempted_at: datetime = SQLField(index=True)
```

**Features:**
- Automatic attempt tracking during practice sessions
- Subject and system performance breakdowns
- Difficulty analysis
- Question timing analytics
- Daily activity streaks
- Percentile rankings across all users
- Weak area identification
- Integrated with `PracticeSessionContext` for seamless tracking

**Files:**
- `src/analytics/user_models.py` - Database and API models
- `src/analytics/user_store.py` - Analytics computation and storage
- `src/analytics/user_app.py` - FastAPI endpoints (port 8008)
- `web/src/components/UserAnalyticsDashboard.tsx` - Frontend dashboard

**Integration:**
- Automatically records attempts via `PracticeSessionContext.completeSession()`
- Non-blocking async recording
- Works with tutor, timed, and practice modes

---

### 7. Assessment System (`src/assessments/`)
**Status:** ✅ Complete
**Database:** `data/assessments.db`
**Table:** `assessments`

**Model:**
```python
class AssessmentDB(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    assessment_id: str = SQLField(unique=True, index=True)
    candidate_id: str = SQLField(index=True)

    # Blueprint configuration (JSON)
    subject: Optional[str]
    system: Optional[str]
    difficulty: Optional[str]
    tags: str = SQLField(sa_column=Column(JSON), default="[]")
    time_limit_minutes: int = 280

    # Status and timestamps
    status: str = SQLField(default="created", index=True)
    created_at: datetime
    started_at: Optional[datetime]
    expires_at: Optional[datetime]
    submitted_at: Optional[datetime]

    # Question delivery and responses (JSON)
    question_ids: str = SQLField(sa_column=Column(JSON), default="[]")
    responses: str = SQLField(sa_column=Column(JSON), default="{}")

    # Scoring
    total_questions: int = 0
    correct: int = 0
    incorrect: int = 0
    omitted: int = 0
    percentage: float = 0.0
    duration_seconds: Optional[int]
```

**Features:**
- Full assessment lifecycle (create, start, submit, score)
- Blueprint-based question selection
- Timed assessment tracking with expiration
- Response persistence
- Automatic scoring
- Timezone-aware datetime handling

**Files:**
- `src/assessments/db_models.py` - Database models
- `src/assessments/db_store.py` - Database operations
- `src/assessments/db_app.py` - FastAPI endpoints (port 8002)
- `tests/test_assessment_database.py` - 20 comprehensive tests

**Migration Impact:**
- ✅ All tests passing
- ✅ Compatible with existing frontend (SelfAssessmentRoute)
- ✅ Data persists across server restarts

---

### 8. Medical Library & Notebook (`src/library/`)
**Status:** ✅ Complete
**Database:** `data/library.db`
**Tables:**
- `articles` - Medical reference articles
- `notebook_entries` - User notes with resource linking

**Models:**
```python
class ArticleDB(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    article_id: str = SQLField(unique=True, index=True)
    title: str = SQLField(max_length=500, index=True)
    summary: str = SQLField(sa_column=Column(Text))
    body: str = SQLField(sa_column=Column(Text))
    tags: str = SQLField(sa_column=Column(JSON), default="[]")
    bookmarked: bool = SQLField(default=False, index=True)
    created_at: datetime
    updated_at: datetime

class NotebookEntryDB(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    note_id: str = SQLField(unique=True, index=True)
    user_id: Optional[int] = SQLField(index=True)
    title: str
    body: str = SQLField(sa_column=Column(Text))
    tags: str = SQLField(sa_column=Column(JSON), default="[]")
    bookmarked: bool = SQLField(default=False, index=True)

    # Linked resources (JSON arrays)
    article_ids: str = SQLField(sa_column=Column(JSON), default="[]")
    question_ids: str = SQLField(sa_column=Column(JSON), default="[]")
    video_ids: str = SQLField(sa_column=Column(JSON), default="[]")

    created_at: datetime
    updated_at: datetime
```

**Features:**
- Article management (CRUD operations)
- Notebook entries with multi-resource linking
- Tag-based organization
- Bookmark functionality
- Search and filtering
- JSON fields for flexible resource arrays

**Files:**
- `src/library/db_models.py` - Database models
- `src/library/db_store.py` - Database operations
- `src/library/db_app.py` - FastAPI endpoints (port 8004)
- `web/src/components/QuickNote.tsx` - Embedded note-taking widget
- `web/src/components/NotebookWorkspace.tsx` - Full notebook interface
- `tests/test_library_database.py` - 29 comprehensive tests

**Integration:**
- QuickNote component integrated into VideoPlayer (with timestamp support)
- QuickNote component integrated into QuestionViewer
- Automatic resource linking based on context

**Migration Impact:**
- ✅ All tests passing
- ✅ Notebook accessible from video player and question viewer
- ✅ Data persists across server restarts

---

## 📊 Migration Summary

| Service | Before | After | Data Loss Risk | Status |
|---------|--------|-------|----------------|--------|
| **Users** | N/A | ✅ SQLite | None | ✅ Complete |
| **Reviews** | ✅ SQLite | ✅ SQLite | None | ✅ Complete |
| **Study Planner** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Flashcards** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Videos** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Analytics** | N/A | ✅ SQLite | None | ✅ Complete |
| **Assessments** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Library/Notes** | ❌ In-memory | ✅ SQLite | **FIXED** | ✅ Complete |
| **Questions** | ✅ JSON files | ✅ JSON files | None (read-only) | No migration needed |

---

## 🎉 All Migrations Complete!

All services now use proper database persistence. Data is preserved across server restarts, and the platform is ready for multi-user deployment.

### Future Enhancement: Unified Database
**Long-term goal:** Consolidate all databases into a single database with proper foreign key relationships.

**Current State:**
```
data/
├── users.db          # User authentication
├── planner.db        # Study plans and tasks
├── flashcards.db     # Flashcard decks, cards, and reviews
├── videos.db         # Videos, playlists, progress, bookmarks
├── analytics.db      # User performance analytics
├── assessments.db    # Self-assessment system
├── library.db        # Medical articles and notebook entries
├── reviews/          # Review workflow (multiple DBs)
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
- ❌ Data lost on server restart (in-memory storage)
- ❌ No multi-user support (no data isolation)
- ❌ No query capabilities (everything in memory)
- ❌ Poor scalability

### After All Migrations:
- ✅ **All data persists across restarts**
- ✅ **Full multi-user support** with user_id indexes
- ✅ **Powerful SQL queries** (filter, sort, paginate, aggregate)
- ✅ **Better performance** with database indexes
- ✅ **Comprehensive analytics** tracking user progress
- ✅ **Integrated note-taking** across all resources
- ✅ **Spaced repetition learning** with SM-2 algorithm
- ✅ **Video progress tracking** with bookmarks
- ✅ **Assessment persistence** with full lifecycle management

---

**Last Updated:** 2025-11-01
**Status:** ✅ **Complete** - All planned migrations finished. Platform ready for production deployment.
