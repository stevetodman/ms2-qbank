UWorld USMLE Step 1 - Complete Product Requirements Document & Wireframes Executive Summary
UWorld USMLE Step 1 is a comprehensive medical exam preparation platform featuring 3,600+ practice questions, detailed explanations, self-assessments, flashcards, study planning tools, and performance analytics. The platform helps medical students prepare for the USMLE Step 1 exam through realistic question simulation, active learning, and personalized study management.
Core Value Proposition: Transform complex medical concepts into testable knowledge through realistic exam simulation and expert-crafted content.

PRODUCT OVERVIEW
1.1 Target Users
Primary: Medical students (M1-M2) preparing for USMLE Step 1
Secondary: Pre-clinical students seeking curriculum support
Tertiary: Medical educators using the Learning Platform (LP)

1.2 Core Features

Question Bank (QBank) - 3,600+ USMLE-style questions
Self-Assessments - 3 simulated practice exams (160 questions each)
Flashcards - ReadyDecks (2,000+ premade) + SmartCards (custom)
Medical Library - Peer-reviewed articles integrated with QBank
Study Planner - Automated scheduling tool
My Notebook - Integrated note-taking system
Performance Analytics - Real-time progress tracking
Video Library - High-yield visual learning content

1.3 Platform Access

Web application (desktop/laptop)
iOS mobile app
Android mobile app
Cross-device synchronization

INFORMATION ARCHITECTURE
UWorld USMLE Step 1 Platform
│
├── Dashboard (Home)
│   ├── Quick Stats Overview
│   ├── Daily Tasks (from Study Planner)
│   ├── Recent Activity
│   └── Performance Snapshot
│
├── QBank
│   ├── Create Test
│   │   ├── Test Mode Selection (Timed/Tutor/Custom)
│   │   ├── Question Selection
│   │   │   ├── By Subject (Anatomy, Biochemistry, etc.)
│   │   │   ├── By System (Cardiovascular, Respiratory, etc.)
│   │   │   ├── By Topic (Specific diseases/concepts)
│   │   │   └── By Status (Unused/Incorrect/Marked/Omitted)
│   │   └── Block Size (1-200 questions)
│   │
│   │   ├── Question Interface
│   │   │   ├── Question Display
│   │   │   ├── Answer Choices
│   │   │   ├── Navigation Controls
│   │   │   ├── Mark/Suspend/Notes
│   │   │   └── Timer/Block Info
│   │
│   │   └── Answer Explanation
│   │       ├── Detailed Rationale
│   │       ├── Visual Content (Images/Charts/Tables)
│   │       ├── References/Hyperlinks
│   │       ├── Related Questions
│   │       ├── Add to Notebook
│   │       ├── Create Flashcard
│   │       └── Report Issue
│
├── Self-Assessments
│   ├── Available Forms (Form 1, 2, 3)
│   ├── Start Assessment
│   ├── Assessment Interface
│   └── Score Report
│       ├── 3-Digit Score Prediction
│       ├── Percentile Ranking
│       ├── Subject Breakdown
│       └── System Breakdown
│
├── Flashcards
│   ├── ReadyDecks (Premade)
│   │   ├── Browse by System
│   │   ├── Review Session
│   │   └── Spaced Repetition
│   │
│   │   └── SmartCards (Custom)
│   ├── Create New Card
│   ├── Import from QBank
│   ├── Organize Decks
│   └── Study Mode
│
├── Medical Library
│   ├── Browse Articles
│   │   ├── By Topic
│   │   ├── By System
│   │   └── Search
│   │
│   │   ├── Article View
│   │   │   ├── Content Display
│   │   │   ├── Related Questions
│   │   │   ├── Bookmark
│   │   │   └── Add to Notebook
│   │
│   │   └── Bookmarked Articles
│
├── Study Planner
│   ├── Setup/Configuration
│   │   ├── Exam Date
│   │   ├── Study Hours/Week
│   │   ├── Goals (Coverage, Repetition)
│   │   └── Subject Priorities
│   │
│   │   ├── Daily Schedule View
│   ├── Calendar View
│   ├── Task Management
│   └── Progress Tracking
│
├── My Notebook
│   ├── Create/Edit Notes
│   ├── Organize (Tabs/Pages)
│   ├── Import from QBank
│   ├── Add Media/Tables
│   ├── Tagging System
│   └── Search Notes
│
├── Performance
│   ├── Overall Statistics
│   │   ├── Questions Completed
│   │   ├── Overall % Correct
│   │   ├── Time per Question
│   │   └── Percentile Rank
│   │
│   │   ├── Subject Performance
│   ├── System Performance
│   ├── Test History
│   ├── Graphs & Charts
│   └── Peer Comparison
│
├── Videos
│   ├── Browse by Topic/System
│   ├── Video Player
│   ├── Playlist Management
│   └── Related Content
│
├── Help & Support
│   ├── How to Use Guide
│   ├── FAQs
│   ├── Contact Support
│   └── Product Tour
│
└── Account Settings
    ├── Profile Information
    ├── Subscription Details
    ├── Notification Preferences
    ├── Display Settings
    └── Device Management

DETAILED WIREFRAMES
3.1 DASHBOARD (HOME SCREEN)
┌─────────────────────────────────────────────────────────────────────────┐
│ UWorld USMLE Step 1 [Search] [Notifications] [Profile]│
├─────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [QBank] [Self-Assessment] [Flashcards] [Library] [More ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Welcome back, [Student Name]! Day 45 of 180                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25%           │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ TODAY'S TASKS [View Planner]                                   │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │ ☐ Complete 40 Questions - Cardiovascular System                │ │
│ │ │ ☐ Review 50 Flashcards - Pharmacology                          │ │
│ │ │ ☐ Watch Video: Cardiac Cycle                                   │ │
│ │ │ ☐ Review Incorrect Questions from Yesterday                    │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐     │
│ │ OVERALL PROGRESS │ │ RECENT ACTIVITY │ │ PERFORMANCE │     │
│ ├────────────────────┤ ├────────────────────┤ ├────────────────────┤     │
│ │ Questions: 1,840 │ │ Yesterday:       │ │ Overall: 62%        │     │
│ │ Completed: 51%   │ │ • 40 Questions   │ │ Percentile: 68th    │     │
│ │                  │ │   (68% correct)  │ │ Avg Score: 62%      │     │
│ │                  │ │ • 30 Flashcards  │ │ Improvement: +8%    │     │
│ │                  │ │ • 2 Videos       │ │ (last 30 days)      │     │
│ │ Time/Q: 1m 45s   │ │                  │ │                     │     │
│ │ [View Details]   │ │ [See All Activity] │ [Full Analytics]    │     │
│ └────────────────────┘ └────────────────────┘ └────────────────────┘     │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ QUICK ACTIONS                                                   │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │ [Create New Test] [Review Incorrect] [Continue Last Test]       │ │
│ │ │ [Study Flashcards] [Take Self-Assessment] [Browse Medical Library]│
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ WEAK AREAS (Needs Improvement)                                  │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │ • Pharmacology: Autonomic Drugs (45% correct)                   │ │
│ │ │ • Biochemistry: Metabolism (48% correct)                        │ │
│ │ │ • Pathology: Neoplasia (52% correct)                            │ │
│ │ │ [Create Focused Test]                                          │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ ANNOUNCEMENTS & TIPS                                            │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │ 💡 New Content: 50 questions added to Immunology               │ │
│ │ │ 📚 Study Tip: Review your incorrect questions daily for retention│
│ │ │ 🎯 You're on track! Keep up the great work!                     │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
3.2 CREATE TEST (QBANK)
┌─────────────────────────────────────────────────────────────────────────┐
│ UWorld USMLE Step 1 > QBank > Create Test                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ CREATE NEW TEST                                                         │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ STEP 1: SELECT TEST MODE                                        │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ ○ TIMED MODE                                                   │ │
│ │ │ Simulates actual exam conditions with time limits              │ │
│ │ │ Cannot see answers until block is complete                     │ │
│ │ │ Recommended for exam simulation                                │ │
│ │ │                                                                 │ │
│ │ │ ● TUTOR MODE (Selected)                                        │ │
│ │ │ See explanations immediately after each question               │ │
│ │ │ Can pause and resume at any time                               │ │
│ │ │ Best for learning and understanding concepts                   │ │
│ │ │                                                                 │ │
│ │ │ ○ CUSTOM MODE                                                  │ │
│ │ │ Customize timing and explanation settings                      │ │
│ │ │ Flexible options for your study preferences                    │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ STEP 2: SELECT QUESTIONS                                        │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ Filter by: [SUBJECT ▼] [SYSTEM ▼] [STATUS ▼] [DIFFICULTY ▼]    │ │
│ │ │                                                                 │ │
│ │ │ ┌─────────────────────┬─────────────────────┬──────────────┐    │ │
│ │ │ │ SUBJECTS            │ SYSTEMS             │ STATUS       │    │ │
│ │ │ ├─────────────────────┼─────────────────────┼──────────────┤    │ │
│ │ │ │ ☑ All Subjects      │ ☑ All Systems       │ ○ All        │    │ │
│ │ │ │ ☐ Anatomy (180)     │ ☐ Cardiovascular    │ ○ Unused     │    │ │
│ │ │ │ ☐ Behavioral (220)  │ ☐ Endocrine         │ ○ Incorrect  │    │ │
│ │ │ │ ☐ Biochemistry(310) │ ☐ GI/Nutrition      │ ○ Marked     │    │ │
│ │ │ │ ☐ Biostatistics(210)│ ☐ Heme/Lymph        │ ○ Omitted    │    │ │
│ │ │ │ ☑ Immunology (180)  │ ☐ Musculoskeletal   │              │    │ │
│ │ │ │ ☐ Microbiology(390) │ ☐ Nervous/Special   │              │    │ │
│ │ │ │ ☐ Pathology (520)   │ ☐ Renal/Urinary     │              │    │ │
│ │ │ │ ☐ Pharmacology(450) │ ☐ Reproductive      │              │    │ │
│ │ │ │ ☐ Physiology (420)  │ ☐ Respiratory       │              │    │ │
│ │ │ │                     │ ☐ Skin/Connective   │              │    │ │
│ │ │ │                     │ ☐ Multisystem       │              │    │ │
│ │ │ └─────────────────────┴─────────────────────┴──────────────┘    │ │
│ │ │                                                                 │ │
│ │ │ Selected: Immunology                                           │ │
│ │ │ Available Questions: 180 | Completed: 65 | Remaining: 115       │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ STEP 3: NUMBER OF QUESTIONS                                    │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ Number of questions: [40 ▼]                                    │ │
│ │ │                                                                 │ │
│ │ │ Quick Select: [10] [20] [40] [60] [80] [100] [Custom]          │ │
│ │ │                                                                 │ │
│ │ │ 💡 Tip: 40 questions simulates one block of the actual exam     │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ ADVANCED OPTIONS [Show]                                         │     │
│ │ │                                                                 │ │
│ │ │ ☐ Randomize question order                                     │ │
│ │ │ ☐ Randomize answer choices                                     │ │
│ │ │ ☐ Include images/media                                         │ │
│ │ │ ☐ Show question ID                                             │ │
│ │ │ ☐ Enable calculator                                            │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ [Cancel] [Create Test →]                                               │
└─────────────────────────────────────────────────────────────────────────┘
3.3 QUESTION INTERFACE (DURING TEST)
┌─────────────────────────────────────────────────────────────────────────┐
│ Test Block 1 [Lab Values] [Calculator] [?Help]                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Question 15 of 40 Time Remaining: 52:34 [End Block]                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 37.5%           │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ QUESTION                                                       │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ A 45-year-old man comes to the emergency department because of │ │
│ │ │ severe chest pain for the past 2 hours. He has a history of    │ │
│ │ │ hypertension and hyperlipidemia. His current medications include│ │
│ │ │ lisinopril and atorvastatin. His temperature is 37°C (98.6°F), │ │
│ │ │ pulse is 110/min, respirations are 20/min, and blood pressure  │ │
│ │ │ is 150/95 mm Hg. Physical examination shows diaphoresis and    │ │
│ │ │ anxiety. Cardiac examination shows no abnormalities. An ECG    │ │
│ │ │ shows ST-segment elevation in leads II, III, and aVF.          │ │
│ │ │                                                                 │ │
│ │ │ ┌─────────────────────────────────────┐                         │ │
│ │ │ │ [ECG IMAGE]                         │                         │ │
│ │ │ │                                     │                         │ │
│ │ │ │ Shows ST elevation in               │                         │ │
│ │ │ │ inferior leads                       │                         │ │
│ │ │ └─────────────────────────────────────┘                         │ │
│ │ │ [View Full Size] [Toggle Image]                                 │ │
│ │ │                                                                 │ │
│ │ │ Which of the following arteries is most likely occluded?       │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ ANSWER CHOICES                                                 │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ ○ A. Circumflex artery                                         │ │
│ │ │ ○ B. Left anterior descending artery                           │ │
│ │ │ ● C. Right coronary artery                                     │ │
│ │ │ ○ D. Left main coronary artery                                 │ │
│ │ │ ○ E. Posterior descending artery                               │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ QUESTION TOOLS                                                 │     │
│ │ │                                                                 │ │
│ │ │ [⚑ Mark] [📝 Notes] [⏸ Suspend] [⏭ Skip]                       │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ NAVIGATION                                                     │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │                                                                 │ │
│ │ │ [1][2][3][4][5][6][7][8][9][10][11][12][13][14][●][16][17]... │ │
│ │ │                                                                 │ │
│ │ │ ● Answered ○ Unanswered ⚑ Marked ⏸ Suspended                  │ │
│ │ │                                                                 │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ [← Previous] [Submit →]                                                 │
│ YOUR PLAYLISTS │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ 📁 Watch Later (8 videos)                                       │ │
│ │ 📁 Biochemistry Review (12 videos)                              │ │
│ │ 📁 Weak Topics (15 videos)                                      │ │
│ │ [+ Create Playlist]                                             │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐     │
│ │ RECENTLY WATCHED                                               │     │
│ │ ├─────────────────────────────────────────────────────────────────┤ │
│ │ │ • Glycolysis Overview (Yesterday)                             │ │
│ │ │ • ECG Interpretation Basics (2 days ago)                      │ │
│ │ │ • Antibiotic Mechanisms (3 days ago)                          │ │
│ │ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

USER FLOWS
4.1 New User Onboarding Flow

Account Creation/Login
↓

Welcome Screen

Product tour option
Skip to dashboard
↓

Initial Setup

Enter exam date
Select study availability
Choose priority subjects/systems
↓

Study Plan Generation

AI-generated personalized schedule
Review and customize
↓

Dashboard Landing

Quick start guide
First test recommendations
4.2 Daily Study Session Flow

Dashboard Login
↓

Review Today's Tasks

QBank questions assigned
Flashcard reviews due
Video recommendations
↓

Start QBank Session

Select or use assigned test
Configure settings
Begin questions
↓

Answer Questions

In tutor or timed mode
Mark/suspend/note
↓

Review Explanations (Tutor mode)

Read detailed rationale
View visual content
Save to notebook/flashcards
↓

Complete Session

View performance summary
Update progress tracking
↓

Optional: Review Flashcards
↓

Optional: Watch Videos
↓

End of Day Summary

Tasks completed
Progress toward goals
4.3 Self-Assessment Flow

Navigate to Self-Assessments
↓

Select Form (1, 2, or 3)
↓

Read Instructions

Time limits
Break policy
Score reporting
↓

Start Block 1

40 questions
60-minute timer
↓

Complete 4 Blocks

160 questions total
Can pause between blocks
↓

Submit Assessment
↓

Score Report Generated

3-digit predicted score
Percentile ranking
Subject/system breakdown
↓

Review Explanations

All 160 questions
Detailed rationales
↓

Create Action Plan

Identify weak areas
Adjust study focus
4.4 Question Review and Study Flow

Complete Question
↓

View Explanation (Tutor Mode)
↓

Read Educational Content

Rationale
Visual aids
Related topics
↓

Take Action (Optional):
a. Add to Notebook

Highlight/copy content
Add personal notes
Tag and organize
b. Create Flashcard

Auto-generate from content
Customize Q&A
Add to deck
c. View in Medical Library

Read full article
Bookmark for later
Explore related content
d. Mark for Review

Flag question
Add to review queue
↓

Continue to Next Question

FEATURE SPECIFICATIONS
5.1 Question Bank (QBank)
Core Features:

Question Count: 3,600+ USMLE-style multiple-choice questions
Content Organization:

By Subject: Anatomy, Behavioral Science, Biochemistry, Biostatistics, Immunology, Microbiology, Pathology, Pharmacology, Physiology
By System: Cardiovascular, Endocrine, GI/Nutrition, Hematologic/Lymphatic, Musculoskeletal, Nervous/Special Senses, Renal/Urinary, Reproductive, Respiratory, Skin/Connective Tissue, Multisystem
By Status: Unused, Incorrect, Marked, Omitted, Correct
By Difficulty: Not explicitly shown to users

Test Modes:

Timed Mode

Simulates actual exam timing
Cannot see explanations until block complete
Cannot mark or suspend
Strict time limits (60 min per 40 questions standard)

Tutor Mode

Immediate explanation after each question
No time limit (or relaxed)
Can pause/resume
Mark, suspend, add notes

Custom Mode

User-configurable timing
Flexible explanation display
Custom restrictions

Question Interface Elements:

Timer display (elapsed or remaining)
Progress bar
Question stem with clinical vignette
Images/diagrams/charts embedded
Answer choices (single best answer)
Navigation grid showing all questions
Mark/suspend/notes buttons
Lab values reference
Calculator tool

Answer Explanation Components:

Educational objective statement
Detailed rationale (300-800 words typical)
Correct answer highlighted with ✓
Incorrect answers with explanations marked ❌
High-quality medical illustrations
Tables and comparison charts
Clinical pearls/key concepts boxes
Related topics links
References to medical literature
Actions: Add to Notebook, Create Flashcard, Report Issue
Peer performance statistics
Related questions suggestions

Performance Tracking:

Overall % correct
Time per question
Percentile ranking vs peers
Subject breakdown
System breakdown
Trend over time
Unused/incorrect/marked counters

5.2 Self-Assessments (Practice Exams)
Structure:

3 forms available (Form 1, 2, 3)
Each form: 4 blocks × 40 questions = 160 questions
60 minutes per block
Questions unique to assessments (not in QBank)

Timing Options:

1x speed (standard)
1.5x speed
2x speed (extended time accommodation)
Can pause between blocks

Score Report:

Predicted 3-digit USMLE score
Percentile ranking among UWorld users
Overall % correct
Subject performance breakdown
System performance breakdown
Time per question average
Comparison to previous forms

Recommended Schedule:

Form 1: Baseline (early preparation)
Form 2: Mid-preparation check
Form 3: Final readiness (1-2 weeks before exam)

Post-Assessment:

Full explanations for all 160 questions
Performance analysis tools
Weak area identification
Study plan adjustments

5.3 Flashcards
ReadyDecks™ (Premade):

2,000+ expert-created cards
Organized by body system
Cover high-yield Step 1 concepts
Include images and diagrams
Spaced repetition algorithm
Progress tracking per deck
"Due today" reminders

SmartCards™ (Custom):

User-created flashcards
Quick-create from QBank content
Rich text editor with formatting
Add images, tables, charts
Organize into custom decks
Tag system for categorization
Export/import capability

Study Features:

Spaced repetition scheduling
Confidence-based review
Shuffle mode
Study statistics
Study streaks tracking
Mobile app synchronization

Card Types:

Text-based Q&A
Image-based identification
Cloze deletions
Multi-part questions

5.4 Medical Library
Content:

Peer-reviewed articles
Disease-specific topics
Clinical presentations
Diagnostic approaches
Treatment guidelines
High-yield medical images
Evidence-based content

Organization:

Browse by system
Browse by subject
Search functionality
Recently added
Most popular

Integration:

Links from QBank questions
Related questions displayed
Add directly to Notebook
Cross-references throughout

Article Features:

Professional medical illustrations
Clinical images
Diagnostic algorithms
Treatment flowcharts
Updated regularly (monthly)
References and citations

5.5 Study Planner
Setup:

Exam date input
Study hours per week
Days per week available
Coverage goals (1x, 2x through QBank)
Subject priorities
Weakness focus

Automated Planning:

AI-generated daily tasks
Question allocations
Flashcard reviews
Video recommendations
Milestone scheduling

Calendar Views:

Daily agenda
Weekly overview
Monthly calendar
Progress visualization

Task Management:

Check off completed tasks
Reschedule missed tasks
Add custom tasks
Mark priorities

Progress Tracking:

Questions completed vs. target
Subject coverage %
Days ahead/behind schedule
Milestone completion
Projected completion date

Adaptive Features:

Adjusts to performance
Reallocates time to weak areas
Suggests review sessions
Pace adjustment warnings

5.6 My Notebook
Structure:

Hierarchical organization (notebooks > tabs > pages)
Unlimited entries
Custom naming and categorization
Tagging system

Content Creation:

Rich text editor
Copy content from QBank
Copy images/charts/tables
Insert hyperlinks
Add custom drawings
Upload files

Formatting Options:

Bold, italic, underline
Highlighting (multiple colors)
Bullet lists, numbered lists
Headers (H1, H2, H3)
Font size adjustment
Tables

Organization:

Folder structure
Search functionality
Tag filtering
Sort by date/name/tag
Archive old notes

Integration:

Quick-add from question explanations
Import from Medical Library
Link to related questions
Export to PDF
Print functionality

Persistence:

Auto-save feature
Cloud synchronization
1-year archival after subscription expires
Transfer to next subscription

5.7 Video Library
Content:

High-yield topics
Difficult concepts visualization
Step-by-step processes
Animation of mechanisms
Clinical presentations
Diagnostic techniques

Organization:

Browse by system
Browse by subject
Duration filtering
Recently added
Most viewed

Features:

Playback speed control (0.5x - 2x)
Pause/rewind/fast-forward
Bookmarking timestamps
Note-taking during playback
Closed captions/transcripts

Playlists:

Create custom playlists
Pre-made playlists
Save for later
Share playlists

Integration:

Related questions linked
Add to Study Planner
Save notes to Notebook

5.8 Performance Analytics
Metrics Tracked:

Total questions completed
Overall % correct
Average time per question
Percentile ranking
Subject-level performance
System-level performance
Difficulty performance
Test mode comparison

Visualizations:

Line graphs (trends over time)
Bar charts (subject/system comparison)
Percentile curves
Progress bars
Heat maps

Comparisons:

vs. Peer average
vs. Own baseline
vs. Previous week/month
vs. Target score

Insights:

Weak area identification
Improvement suggestions
Study recommendations
Readiness indicators

Data Export:

CSV export
PDF reports
Print-friendly formats
Custom date ranges

TECHNICAL SPECIFICATIONS
6.1 Platform Requirements
Web Application:
Browser Compatibility: Chrome, Firefox, Safari, Edge (latest 2 versions)
Responsive Design: Breakpoints at 768px, 1024px, 1440px
Progressive Web App (PWA) capability
Offline mode for saved content

Mobile Applications:

iOS: Version 14.0+
Android: Version 8.0+
Native apps with full feature parity
Offline question bank access
Background synchronization

Cross-Platform:

Account synchronization (real-time)
Progress saves across devices
Bookmarks and notes sync
Flashcard progress sync

6.2 Performance Requirements
Page Load:

Dashboard: < 2 seconds
Question load: < 1 second
Explanation render: < 1.5 seconds
Image load: < 2 seconds (lazy loading)

Search:

Results in < 500ms
Auto-suggestions in < 200ms

Data Sync:

Cross-device: < 5 seconds
Progress save: Real-time

Uptime:

99.9% availability
Scheduled maintenance windows
Redundancy and failover

6.3 Security & Privacy
Authentication:

Secure login (email + password)
Two-factor authentication (optional)
Session management (30-day remember me)
Password requirements (8+ chars, mixed case, numbers)

Data Protection:

HTTPS encryption (TLS 1.3)
Data encryption at rest
HIPAA-compliant (no PHI stored)
Regular security audits

Privacy:

Anonymous performance data
Optional data sharing for peer comparison
GDPR compliance
FERPA compliance

Account Security:

Device management
Active session monitoring
Logout all devices option
Account recovery process
6.4 Content Management
Question Updates:

Monthly content updates
Real-time error corrections
Version control
User feedback integration

Content Quality:

Physician-authored
Peer-reviewed
Aligned with USMLE content outline
Evidence-based references

Media Assets:

High-resolution images
SVG diagrams (scalable)
Video compression (adaptive bitrate)
Lazy loading implementation

6.5 Analytics & Tracking
User Analytics:

Study time tracking
Feature usage metrics
Question performance
Abandonment points

Performance Metrics:

System latency
Error rates
User satisfaction scores
Support ticket patterns

6.6 Integration Points
External Tools:

Calendar integration (Google, Outlook)
Note export (Evernote, OneNote)
Anki compatibility
Email notifications

Internal Integration:

QBank ↔ Flashcards
QBank ↔ Notebook
QBank ↔ Medical Library
Study Planner ↔ All modules
Performance ↔ Study Planner (adaptive)

USER EXPERIENCE DESIGN
7.1 Design Principles
Clarity:
Clean interface
Minimal distractions during testing
Clear hierarchy
Intuitive navigation

Efficiency:
Quick access to key features
Keyboard shortcuts
One-click actions
Smart defaults

Consistency:
Uniform design language
Predictable interactions
Standard UI components
Cohesive visual identity

Accessibility:
WCAG 2.1 Level AA compliance
Screen reader support
Keyboard navigation
High contrast mode
Adjustable font sizes

7.2 Visual Design
Color Palette:

Primary: Medical blue (#0066CC)
Secondary: Success green (#28A745)
Accent: Warning amber (#FFC107)
Error: Alert red (#DC3545)
Neutral: Gray scale (#F8F9FA to #212529)

Typography:

Headers: Sans-serif (Source Sans Pro)
Body: Serif for long-form content (Merriweather)
Monospace: Code/formulas (Courier New)
Sizes: 14px base, 18px headers, 12px captions

Icons:

Material Design icon set
Consistent 24px grid
Simple, recognizable shapes
Accessibility labels

7.3 Interaction Patterns
Feedback:

Loading states (skeleton screens)
Success confirmations
Error messages (actionable)
Progress indicators
Tooltips and help text

Navigation:

Persistent top navigation
Breadcrumbs for deep navigation
Back button support
Quick links/shortcuts

Forms:

Inline validation
Clear error messages
Auto-save capability
Progress indication

CONTENT SPECIFICATIONS
8.1 Question Format
Structure:

Clinical vignette (2-6 sentences)
Patient demographics
Chief complaint
History of present illness
Past medical history
Medications
Physical exam findings
Laboratory/imaging results
Lead-in question

Answer Choices:

4-5 options (typically 5)
Single best answer
Plausible distractors
Alphabetical order when appropriate
No "all of the above" or "none of the above"

Difficulty Distribution:

Easy: 20%
Medium: 60%
Hard: 20%

Content Coverage:

Aligned with USMLE Step 1 Content Outline
Updated annually
Covers all subjects and systems proportionally

8.2 Explanation Format
Components:

Educational Objective (1 sentence)
Clinical Analysis (2-4 paragraphs)

Case presentation review
Key findings
Differential diagnosis
Diagnostic reasoning

Correct Answer Explanation

Why it's correct
Supporting evidence

Incorrect Answer Explanations

Why each is wrong
When they might be correct

Visual Aids

Diagrams, charts, tables
Medical images
Comparison graphics

Clinical Pearls (2-4 bullet points)
Related Topics (hyperlinked)
References (peer-reviewed)

Writing Standards:

Clear, concise language
Active voice
Medical terminology with definitions
Step-by-step reasoning
Evidence-based
Current guidelines (< 2 years old)

8.3 Visual Content
Images:

High resolution (minimum 1200px width)
Labeled anatomical structures
Color-coded for clarity
Source attribution

Charts and Graphs:

Clean design
Color-blind friendly
Large fonts
Clear legends

Tables:

Comparison tables
Differential diagnosis
Drug classifications
Lab value ranges
Reference material

BUSINESS MODEL
9.1 Subscription Plans
Standard Plans:

3 months: $179
6 months: $279
12 months: $449

Features Included:

Full QBank access (3,600+ questions)
3 Self-Assessments
ReadyDecks flashcards
SmartCards (unlimited custom)
Medical Library
Study Planner
My Notebook
Video Library
Performance Analytics
Mobile apps
Email support

Add-Ons:

Additional self-assessments
Extended subscription time
Group/institutional licenses

9.2 Target Metrics
User Engagement:

Daily active users: 60%+
Questions per day: 40+ average
Session length: 90+ minutes
Return rate: 85%+

Outcomes:

Pass rate correlation: 45-50% UWorld = Pass
User satisfaction: 4.5+/5.0
Completion rate: 70%+ finish QBank once
Recommendation NPS: 80+

9.3 Competitive Advantages

Question Quality: Physician-authored, above exam difficulty
Explanation Depth: Industry-leading rationales
Visual Content: Best-in-class illustrations
Integration: Seamless feature ecosystem
Performance Tracking: Detailed analytics
Mobile Experience: Full-featured apps
Content Updates: Monthly additions
Support: Responsive customer service

FUTURE ENHANCEMENTS
10.1 Planned Features
AI-Powered Study:

Personalized question recommendations
Intelligent scheduling optimization
Predictive performance modeling
Weak area auto-detection

Social Learning:

Study groups
Question discussions
Peer teaching tools
Leaderboards (optional)

Enhanced Content:

Video explanations for every question
3D anatomical models
Interactive diagrams
Simulation cases

Advanced Analytics:

Machine learning insights
Score prediction algorithms
Optimal study path calculation
Fatigue detection

10.2 Integration Opportunities

Learning management systems (LMS)
Medical school curricula
Shelf exam preparation
USMLE Step 2/3 continuity
Board certification prep

10.3 Platform Evolution

AR/VR clinical scenarios
Voice-controlled study
Adaptive difficulty
Gamification elements
Live tutoring integration

SUCCESS METRICS
11.1 User Metrics
Acquisition:

New signups per month
Conversion rate (trial → paid)
Marketing ROI
Referral rate

Engagement:

Daily/weekly/monthly active users
Average session duration
Questions completed per user
Feature adoption rates
Churn rate

Satisfaction:

Net Promoter Score (NPS)
Customer satisfaction (CSAT)
App store ratings
Support ticket volume
User testimonials

11.2 Learning Outcomes
Performance:

Average QBank score
Score improvement over time
Subject mastery rates
Self-assessment scores

Exam Results:

Pass rate correlation
Score predictions accuracy
User-reported outcomes
Before/after comparisons

11.3 Business Metrics
Revenue:

Monthly recurring revenue (MRR)
Average revenue per user (ARPU)
Lifetime value (LTV)
Customer acquisition cost (CAC)

Growth:

Year-over-year growth
Market share
Expansion into new markets
Institutional partnerships

SUPPORT & DOCUMENTATION
12.1 User Support Channels:

Email support (support@uworld.com)
In-app help center
FAQ database
Video tutorials
Product tour

Response Times:

Critical issues: < 4 hours
General inquiries: < 24 hours
Content errors: < 48 hours
Feature requests: Acknowledged < 7 days

12.2 Documentation
User Guides:

Getting started guide
Feature tutorials
Study strategy guides
FAQ comprehensive list
Troubleshooting guides

Technical Docs:

System requirements
Browser compatibility
Mobile app specs
API documentation (for institutions)

Study Resources:

Sample study schedules
How to use UWorld effectively
Integration with other resources
Test-taking strategies

IMPROVEMENT OPPORTUNITIES
Based on this comprehensive PRD, here are potential areas for enhancement:
13.1 User Experience Opportunities:

Simplified Onboarding: Reduce setup friction with AI-driven auto-configuration
Smart Question Selection: AI recommends next best question based on performance
Micro-Learning: 10-minute focused sessions for busy students
Voice Notes: Speak notes instead of typing
Offline Mode Enhancement: Full offline access including explanations

13.2 Content & Features Opportunities:

Video Explanations: Every question gets a video walkthrough
Interactive Diagrams: Click-to-explore anatomical models
Spaced Repetition for Questions: Auto-schedule incorrect question reviews
Peer Comparison: Anonymous study groups and competition
Real-Time Tutoring: Live expert help during study sessions

13.3 Analytics & Intelligence Opportunities:

Predictive Analytics: ML model predicts pass probability weekly
Optimal Study Path: AI calculates most efficient question sequence
Fatigue Detection: Recommends breaks based on performance decline
Weak Area Deep Dive: Auto-generates targeted mini-courses
Performance Benchmarking: Compare to students at similar stage

13.4 Collaboration & Social Opportunities:

Study Buddy Matching: Connect with peers at similar level
Question Discussion Forums: Community-driven explanations
Expert Q&A Sessions: Weekly live sessions with physicians
Shared Notebooks: Collaborative note-taking
Achievement System: Badges, streaks, milestones

13.5 Accessibility & Inclusion Opportunities:

Multi-Language Support: Spanish, Mandarin, Hindi options
Text-to-Speech: Listen to questions and explanations
Dark Mode: Eye strain reduction for long study sessions
Dyslexia-Friendly Fonts: Accessibility improvements
Extended Time Simulation: Better accommodation support

13.6 Technical Infrastructure Opportunities:

Progressive Web App: Full offline capabilities
API Access: For institutions and developers
Blockchain Verification: Tamper-proof performance records
Cloud Saves: Unlimited backup and version history
Cross-Platform Sync: Real-time across all devices

CONCLUSION
This comprehensive PRD and wireframe document provides a complete blueprint of the UWorld USMLE Step 1 platform. The platform's strength lies in its integrated ecosystem of high-quality content, intelligent study tools, and performance analytics that work together to optimize medical student exam preparation.

Key Strengths:

Industry-leading question quality and explanations
Comprehensive feature integration
Robust performance tracking
Cross-platform synchronization
Proven learning outcomes

Areas for Innovation:

AI-powered personalization
Enhanced collaboration features
Richer multimedia content
Advanced predictive analytics
Expanded accessibility features

This document serves as both a comprehensive reference for understanding the current platform and a foundation for planning strategic improvements to maintain market leadership and better serve medical students preparing for USMLE Step 1.


## Search API

The Search API exposes the question metadata index over HTTP for integration with web and mobile clients.

1. Install dependencies (ideally in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
2. Start the FastAPI service with Uvicorn:
   ```bash
   uvicorn src.search.app:app --reload
   ```
3. The service will read question data from `data/questions/` and expose a `POST /search` endpoint supporting keyword, tag, and metadata filters. You can interact with the OpenAPI docs at `http://127.0.0.1:8000/docs` once the server is running.
