# Assessment workflow

The assessment service powers simulated exams built around the existing
question dataset. Learners launch a 160-question timed session from the web
application, submit their answers, and immediately review a scored summary.
Each completion feeds the analytics pipeline so longitudinal metrics remain
current.

## FastAPI service

The backend service lives in `src/assessments/` and exposes the following
endpoints:

| Endpoint | Description |
| --- | --- |
| `POST /assessments` | Creates a new assessment blueprint with optional subject, system, difficulty, and tag filters. |
| `POST /assessments/{id}/start` | Selects (and cycles, when necessary) 160 questions that match the blueprint and returns the timed delivery payload. |
| `POST /assessments/{id}/submit` | Scores the submitted responses, persists the attempt, and records analytics events. |
| `GET /assessments/{id}/score` | Returns the canonical score summary for completed attempts. |

The service reuses the shared `AnalyticsService` to publish `/analytics/health`
and writes completion events through the new
`analytics.hooks.AssessmentAnalyticsHook`. Every submission appends a
JSON Lines entry to `data/analytics/events/assessment_completions.jsonl` and
requests a fresh analytics generation, ensuring dashboards stay synchronised
with assessment usage.

## Frontend experience

`web/src/routes/AssessmentRoute.tsx` wires together three components:

- `AssessmentSetupForm` collects exam filters, duration, and learner context.
- `AssessmentDelivery` runs the timed session, handling countdowns, question
  navigation, and auto-submission on timeout.
- `AssessmentSummary` reports the final score and encourages learners to
  restart.

The route also imports `useAssessmentAnalytics`, which refreshes the latest
analytics snapshot after each completion so the homepage dashboard reflects the
new activity without manual reloads.

## Analytics integration and roadmap alignment

Assessment completions expand the analytics inputs beyond review events. The
recorded summaries allow the scheduler to regenerate
`data/analytics/*` artifacts with up-to-date usage distribution. Future roadmap
work can extend the event schema to correlate assessment scores with practice
modes or review outcomes, enriching the learner insights surfaced in
`docs/analysis/question-metrics.*` and the on-platform analytics dashboard.
