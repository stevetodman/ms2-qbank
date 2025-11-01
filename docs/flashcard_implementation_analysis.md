# Flashcard Implementation Analysis - MS2 QBank

## Executive Summary

Based on a thorough codebase review, **flashcard functionality is almost entirely missing** from the MS2 QBank implementation. While the PRD contains comprehensive flashcard requirements, only the frontend routing stub exists.

## PRD Flashcard Requirements (from README.md)

### ReadyDecks (Premade Cards)
- 2,000+ expert-created flashcards
- Organized by body system
- Cover high-yield Step 1 concepts
- Include images and diagrams
- Spaced repetition algorithm
- Progress tracking per deck
- "Due today" reminders

### SmartCards (Custom Cards)
- User-created flashcards
- Quick-create from QBank content
- Rich text editor with formatting
- Add images, tables, charts
- Organize into custom decks
- Tag system for categorization
- Export/import capability

### Study Features
- Spaced repetition scheduling
- Confidence-based review
- Shuffle mode
- Study statistics
- Study streaks tracking
- Mobile app synchronization

### Card Types
- Text-based Q&A
- Image-based identification
- Cloze deletions
- Multi-part questions

## Current Implementation Status

### IMPLEMENTED (Minimal)
1. **Frontend Route** (`/home/user/ms2-qbank/web/src/routes/FlashcardsRoute.tsx`)
   - Basic placeholder component
   - Navigable from main app
   - Contains placeholder text: "The flashcard workspace is under construction"
   - Mentions spaced repetition and deck curation but no actual functionality

2. **Navigation Integration** (`/home/user/ms2-qbank/web/src/components/layout/AppLayout.tsx`)
   - Flashcards menu link
   - Dashboard link to flashcards page

3. **Dashboard References**
   - Mock action for "Review flashcards"
   - Placeholder announcement about flashcard content

### MISSING - Backend Services

#### 1. Flashcard Data Models & Schema
**Files that should exist but don't:**
- `/src/flashcards/models.py` - Pydantic models for:
  - `FlashcardData` - individual card content
  - `DeckMetadata` - deck organization
  - `ReviewRecord` - study history per card
  - `SpacedRepetitionState` - SR algorithm state
  - `CardType` enum (Text, Image, Cloze, MultiPart)

#### 2. Flashcard Service API
**Missing endpoints:**
```
POST   /flashcards/decks              - Create new deck
GET    /flashcards/decks              - List all decks
GET    /flashcards/decks/{deck_id}    - Get deck details
PUT    /flashcards/decks/{deck_id}    - Update deck
DELETE /flashcards/decks/{deck_id}    - Delete deck

POST   /flashcards/decks/{deck_id}/cards       - Add card to deck
GET    /flashcards/decks/{deck_id}/cards       - Get cards in deck
PUT    /flashcards/cards/{card_id}            - Update card
DELETE /flashcards/cards/{card_id}            - Delete card

POST   /flashcards/cards/from-question/{q_id} - Create card from QBank question
GET    /flashcards/review-schedule            - Get cards due for review
POST   /flashcards/cards/{card_id}/review     - Submit review response
GET    /flashcards/cards/{card_id}/stats      - Get card statistics
```

**Missing file structure:**
- `src/flashcards/app.py` - FastAPI application
- `src/flashcards/models.py` - Pydantic schemas
- `src/flashcards/store.py` - Data persistence
- `src/flashcards/service.py` - Business logic

#### 3. Spaced Repetition Algorithm
**Not implemented:**
- SM-2 algorithm (SuperMemo) - most common for SRS
- SM-18 variant - adapted for medical learning
- Interval calculation engine
- Next review date scheduler
- Difficulty factor tracking per card
- Ease factor progression (ease increases/decreases based on performance)

**Expected algorithm components:**
```
- Quality factor: 0-5 scale (user confidence on review)
- Interval: Current time between reviews (days)
- Ease factor: Multiplier for interval (starts at 2.5)
- Next interval = interval * ease_factor
- Ease adjustment: 
  - Quality 4-5: ease increases (+0.1)
  - Quality 2-3: ease decreases slightly
  - Quality 0-1: reset interval to 1 day, decrease ease

- Initial schedule:
  1st review: 1 day
  2nd review: 3 days
  3rd review: 7-16 days
  Then: interval * ease_factor
```

#### 4. Card Creation & QBank Integration
**Missing features:**
- Extract question text as card front
- Extract answer explanation as card back
- Auto-create from question subject/system
- Bulk card creation from test results
- Import incorrect/marked questions as cards
- Link cards back to source questions
- Update cards when questions change

#### 5. Deck Management
**Not implemented:**
- Deck templates (pre-built collections)
- ReadyDecks database/fixtures
- Deck sharing between users
- Public vs. private decks
- Deck statistics aggregation
- Deck progress visualization
- Deck resets/archiving

#### 6. Review Scheduling & Statistics
**Missing:**
- Card review due dates
- Priority queue for reviews
- Daily review limits
- "Due today" scheduling
- Review history persistence
- Streak tracking
- Performance metrics per deck

### MISSING - Frontend Components

1. **Deck Browser** (`/flashcards` main page)
   - ReadyDecks listing
   - SmartCards listing
   - Search/filter decks
   - Create new deck button

2. **Deck Editor**
   - Edit deck title/description
   - Manage cards in deck
   - Reorder cards
   - Set deck options
   - Delete/archive deck

3. **Card Editor**
   - Rich text editor for card content
   - Image upload/embedding
   - Table/chart insertion
   - Multiple card types
   - Tag management

4. **Review Interface**
   - Flash card display
   - Answer reveal
   - Confidence buttons (Very Easy, Easy, Good, Hard, Very Hard)
   - Shuffle option
   - Mark for review
   - Suspend card
   - Progress indicator

5. **Import Dialogs**
   - Import from QBank (by question ID/test)
   - Import marked/incorrect questions
   - Bulk import from CSV
   - Import from Anki format

6. **Statistics Dashboard**
   - Cards learned
   - Cards in progress
   - Cards due today
   - Study streak
   - Performance graphs
   - Time invested

### Data Persistence (Missing)

**Should store in database or JSON files:**
```
data/flashcards/
├── decks.json           - Deck metadata
├── cards.json           - All flashcard content
├── reviews.json         - Review history & SRS state
└── statistics.json      - Aggregated deck stats
```

**Or use database schema:**
```sql
CREATE TABLE decks (
  id UUID PRIMARY KEY,
  user_id UUID,
  name VARCHAR,
  description TEXT,
  deck_type ENUM('ReadyDeck', 'SmartCard'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE flashcards (
  id UUID PRIMARY KEY,
  deck_id UUID REFERENCES decks(id),
  card_type ENUM('text', 'image', 'cloze', 'multipart'),
  front_text TEXT,
  back_text TEXT,
  images JSONB,
  source_question_id UUID,
  tags JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE card_reviews (
  id UUID PRIMARY KEY,
  card_id UUID REFERENCES flashcards(id),
  user_id UUID,
  quality INT (0-5),
  ease_factor DECIMAL,
  interval INT (days),
  next_review_date DATE,
  reviewed_at TIMESTAMP
);
```

## Architecture Gaps

### 1. Service Orchestration
- No flashcard service in `/src/flashcards/`
- Not integrated with analytics service
- No hooks for tracking card reviews
- Not integrated with search API (should index card content)

### 2. Authentication & Authorization
- Not integrated with reviews/auth system
- No multi-user support
- No deck sharing/permissions

### 3. Integration Points Missing
- QBank ↔ Flashcards (card creation)
- Notebook ↔ Flashcards (convert notes to cards)
- Study Planner ↔ Flashcards (schedule reviews)
- Analytics ↔ Flashcards (track performance)

### 4. Data Migration & Fixtures
- No ReadyDeck data (mentioned as 2,000+ cards)
- No migration script for flashcard data
- No import utilities for Anki decks

## Implementation Priority Roadmap

### Phase 1: Core Backend (Weeks 1-2)
1. Create flashcard models & schema
2. Build flashcard service with API endpoints
3. Implement basic CRUD operations for decks/cards
4. Add JSON file storage

### Phase 2: Spaced Repetition (Weeks 2-3)
1. Implement SM-2 algorithm
2. Add review endpoints
3. Calculate next review dates
4. Track ease factors

### Phase 3: Frontend UI (Weeks 3-4)
1. Deck browser & editor
2. Card editor (rich text)
3. Review interface
4. Deck statistics

### Phase 4: QBank Integration (Week 4)
1. Card creation from questions
2. Bulk import from test results
3. Link back to source questions
4. Auto-update when questions change

### Phase 5: ReadyDecks & Polish (Weeks 5-6)
1. Create ReadyDeck fixtures (anatomy, pharmacology, etc.)
2. Implement deck templates
3. Add statistics aggregation
4. Mobile synchronization support

## Estimated Implementation Effort

| Component | Effort | Notes |
|-----------|--------|-------|
| Data Models | 1-2 days | Similar to assessments/reviews |
| FastAPI Service | 3-4 days | Standard CRUD + endpoints |
| Spaced Repetition Algo | 2-3 days | Algorithm implementation + validation |
| Frontend Components | 5-7 days | Rich editor + review interface complex |
| QBank Integration | 2-3 days | Card extraction + linking |
| ReadyDecks Content | 3-5 days | Data creation/curation |
| Testing & Polish | 3-4 days | Unit/integration tests |
| **Total** | **~3-4 weeks** | **Parallel work possible** |

## Comparison to Existing Services

The flashcard service should follow the pattern of existing services:

**Assessment Service** (`src/assessments/`)
```
app.py       - FastAPI routes
models.py    - Pydantic schemas
store.py     - Data persistence
```

**Review Service** (`src/reviews/`)
```
app.py       - FastAPI routes
models.py    - Domain models (ReviewEvent, ReviewRecord)
store.py     - Persistence
auth.py      - Authorization
```

**Flashcard Service** (missing but should be)
```
app.py       - FastAPI routes for deck/card CRUD + review
models.py    - Card, Deck, ReviewRecord, SRState schemas
store.py     - JSON file or DB persistence
scheduler.py - Spaced repetition algorithm
```

## Critical Path Items

1. **Data Model Definition** - Block on everything else
2. **Spaced Repetition Algorithm** - Core differentiator
3. **Basic Review API** - Enables mobile apps
4. **QBank Integration** - High-value feature for users
5. **Frontend Review UI** - Most visible component

## Risks & Considerations

1. **Spaced Repetition Complexity** - SM-2 has many edge cases; thorough testing required
2. **Data Volume** - 2,000+ ReadyDecks requires careful performance optimization
3. **Multi-Device Sync** - Review state must sync across web/mobile
4. **User Confusion** - SmartCards vs ReadyDecks distinction needs clear UX
5. **Content Creation** - ReadyDeck fixtures require medical expertise and effort

## Conclusion

The flashcard feature represents a **major missing piece** of the platform despite being prominently featured in the PRD. It requires:
- Complete backend service from scratch
- Complex spaced repetition algorithm
- Significant frontend development
- Integration with existing QBank service

**Estimated timeline: 3-4 weeks of focused development** with clear phase gates.

---

Generated: 2025-11-01
