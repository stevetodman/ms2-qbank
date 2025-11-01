# Analytics pipeline

The analytics pipeline generates learner-facing metrics from the question bank
and publishes them for both documentation and runtime consumption.

## Command line automation

Use the analytics CLI to generate dashboards on demand or on a schedule:

```bash
python -m analytics.cli \
  --data-dir data/questions \
  --artifact-dir data/analytics \
  --interval 3600
```

Each execution computes the latest metrics, stores timestamped JSON and
markdown artifacts in `data/analytics/`, and refreshes the canonical
`docs/analysis/question-metrics.*` documentation (unless `--skip-docs` is
provided).

The review workflow automatically schedules a regeneration whenever a
question's status transitions between states. Background scheduling debounces
rapid transitions, ensuring the `data/analytics/` artifacts stay current without
manual intervention.

## Production worker

Deployments that run the review API automatically launch the analytics worker
alongside the FastAPI process. Start the service with:

```bash
REVIEWS_JWT_SECRET="change-me" \
uvicorn reviews.app:app --host 0.0.0.0 --port 8000
```

The worker shares the filesystem with the API container, periodically checks
`data/analytics/` for a recent snapshot, and emits a `WARNING` log when the
latest artifact is more than ten minutes old. Operators can query
`GET /analytics/health` to retrieve the most recent generation timestamp and the
current freshness flag.

Artifacts follow the `YYYYMMDDTHHMMSSZ` naming convention. The JSON payload
contains the metrics and the UTC timestamp of generation, while the markdown
file renders the dashboard for quick inspection.

## API surface

The FastAPI service exposes analytics endpoints for consumers and operators:

- `GET /analytics/latest` returns the most recent analytics snapshot.
- `GET /analytics/health` reports whether the background worker has generated a
  fresh snapshot within the last ten minutes.

```bash
curl http://localhost:8000/analytics/latest
```

The response includes:

- `generated_at`: ISO-8601 timestamp of the snapshot (UTC)
- `metrics`: Aggregated counts across difficulty, review status, and usage
- `artifact`: Relative paths to the underlying JSON and markdown files
- `is_fresh`: `true` when the snapshot is less than ten minutes old

If no analytics have been generated yet, the endpoint responds with `404`.

## JSON schemas

Frontend integrations can rely on the following JSON schemas:

| Description | Schema |
| --- | --- |
| Base question metrics structure (used in `question-metrics.json` and within API responses) | [`schemas/question-metrics.schema.json`](schemas/question-metrics.schema.json) |
| Full `/analytics/latest` response payload | [`schemas/latest-analytics-response.schema.json`](schemas/latest-analytics-response.schema.json) |

These schemas are designed for Draft 2020-12 compatible validators.
