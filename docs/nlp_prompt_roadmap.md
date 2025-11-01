# Frontend NLP Prompt Roadmap

This roadmap sequences a series of natural language prompts to guide an LLM-assisted implementation of the frontend. Each prompt references the original product requirements and wireframes outlined in `README.md` to ensure fidelity to the intended user experience.

## Phase 0 – App Shell, Navigation, and Design System
- **Prompt Objective:** Establish the foundational layout, routing, and design system that mirrors the information architecture.
- **Prompt Outline:**
  1. Instruct the model to create `web/src/App.tsx` with React Router routes for Dashboard, QBank, Self-Assessment, Flashcards, Library, Study Planner, Notebook, Performance, Videos, Help & Support, and Account Settings as described in the information architecture tree.
  2. Direct the model to define a shared design system (`web/src/styles/`) including color palette, typography scale, spacing, and elevations that support the wireframe layout hierarchy.
  3. Request layout primitives (`web/src/components/layout/`) for persistent top navigation, collapsible secondary navigation, and responsive grid containers that reflect the dashboard wireframe’s structure.
  4. Emphasize accessibility requirements (ARIA roles, keyboard navigation) consistent with the navigation behaviors implied by the wireframes.

## Phase 1 – Dashboard Experience
- **Prompt Objective:** Build the dashboard widgets and overview panels highlighted in the dashboard wireframes.
- **Prompt Outline:**
  1. Ask the model to implement `web/src/routes/Dashboard.tsx` assembling widgets for daily tasks, quick stats, progress overview, recent activity, performance summary, weak areas, quick actions, and announcements.
  2. Guide creation of reusable widget components (`web/src/components/dashboard/`) that support the checklist, metric cards, and quick action layouts shown in the wireframe blocks.
  3. Provide instructions to generate mock data services in `web/src/services/dashboard.ts` simulating planner tasks, analytics summaries, and announcements until APIs are available.
  4. Include directives for navigation handlers (e.g., “View Planner”, “See All Activity”) matching the interaction affordances shown on the dashboard wireframe.

## Phase 2 – QBank Test Creation and Question Interface
- **Prompt Objective:** Deliver the full QBank creation funnel and question-taking experience described in the IA and detailed frames.
- **Prompt Outline:**
  1. Prompt the model to build `web/src/routes/QBankCreateTest.tsx` with a stepper UI for mode selection (Timed, Tutor, Custom), filtering (subject, system, topic, status, difficulty), and block size selection, mirroring the IA structure.
  2. Define filter components and chip controls in `web/src/components/qbank/filters/` that echo the filter arrangement from the plan.
  3. Specify an interactive question player route (`web/src/routes/QBankSession.tsx`) with timers, answer selection, navigation controls, marking, notes, and suspend/resume features, as outlined in the wireframes.
  4. Outline explanation panels with rationale text, visuals, references, and contextual actions (add to notebook, create flashcard, report issue) aligning with the plan’s answer explanation requirements.

## Phase 3 – Study Tools (Flashcards, Study Planner, Notebook)
- **Prompt Objective:** Implement the interconnected study tools supporting flashcards, planning, and note-taking workflows.
- **Prompt Outline:**
  1. Direct the model to create the Flashcards hub (`web/src/routes/Flashcards.tsx`) with tabs for ReadyDecks browsing/review and SmartCards management, following the IA distinctions.
  2. Describe prompts for building the Study Planner setup wizard and calendar/task views in `web/src/routes/StudyPlanner/`, ensuring scheduling and progress tracking capabilities match the plan.
  3. Instruct on implementing the Notebook workspace (`web/src/routes/Notebook.tsx`) with rich text editing, tab/page organization, tagging, and QBank import hooks per the requirements.
  4. Encourage linking planner tasks to dashboard widgets and exposing flashcard/note creation entry points from QBank explanations, reflecting the cross-feature flows noted in the wireframes.

## Phase 4 – Assessment & Analytics Surfaces
- **Prompt Objective:** Surface self-assessment flows and performance analytics consistent with the reporting expectations.
- **Prompt Outline:**
  1. Guide the model to build self-assessment entry points in `web/src/routes/Assessments.tsx`, including form listings and start flows aligned with the IA.
  2. Detail prompts for designing the assessment-taking interface to share navigation and timer paradigms with the QBank player where appropriate.
  3. Specify creation of score report views (`web/src/routes/AssessmentReport.tsx`) covering three-digit score, percentile, subject/system breakdowns, and historical comparisons as enumerated in the plan.
  4. Request a performance analytics dashboard (`web/src/routes/Performance.tsx`) with charts for overall statistics, trends, peer comparison, and test history, referencing the analytics expectations.

## Phase 5 – Content Library, Media, Support, and Account Management
- **Prompt Objective:** Complete the auxiliary areas described in the IA to round out the learning platform.
- **Prompt Outline:**
  1. Prompt the model to implement the Medical Library (`web/src/routes/Library/`) with browse/search, topic/system filters, and article detail modals mirroring the content hierarchy.
  2. Describe building the Video Library route (`web/src/routes/Videos.tsx`) supporting browsing, playback, and playlist management per the plan.
  3. Include instructions for a Help & Support center (`web/src/routes/Support.tsx`) with guides, FAQs, contact options, and product tour overlays as referenced in the IA.
  4. Direct creation of Account Settings pages (`web/src/routes/AccountSettings/`) covering profile, subscription, notifications, display, and device management while integrating authentication state.

## Prompt Usage Guidance
- Sequence prompts by phase to maintain coherence and allow incremental verification against the wireframes.
- Reinforce references to `README.md` sections (Information Architecture and Detailed Wireframes) within prompts to ensure stylistic and functional alignment.
- Encourage the LLM to generate placeholder data and modular components that can be replaced with live services once backend integration is ready.
- Review outputs after each prompt to validate adherence to the original design intent before advancing to the next phase.

