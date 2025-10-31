# Review workflow data store migration

The review workflow now persists data to a SQLite database powered by
`SQLModel`. If you previously ran the service against the JSON-backed
`review_state.json` file, follow the steps below to migrate to the new
layout.

1. **Create a backup of the JSON file**

   ```bash
   cp data/reviews/review_state.json data/reviews/review_state.json.bak
   ```

2. **Export the existing events**

   The legacy file stores all review activity under the `questions`
   object. Each entry contains the event history for a question. You can
   transform it into SQL insert statements with the helper script below.

   ```bash
   python scripts/migrate_reviews.py data/reviews/review_state.json data/reviews/review_state.db
   ```

   The `scripts/migrate_reviews.py` utility is idempotent and can be
   re-run after manual edits. It automatically normalises missing
   reviewer roles to `reviewer`.

3. **Point the API to the SQLite database**

   Update any configuration that referenced `review_state.json` to use
   the new database file instead:

   ```python
   # Before
   ReviewStore(Path("data/reviews/review_state.json"))

   # After
   ReviewStore(Path("data/reviews/review_state.db"))
   ```

4. **Validate the deployment**

   Run the FastAPI app and issue a few GET/POST requests to confirm the
   history and status are preserved. The API now enforces role-aware
   actions, so ensure that your clients send the appropriate
   `role` attribute with every request.

5. **Monitor analytics integrations**

   The `ReviewStore` now exposes hooks that fire whenever a question's
   status transitions between `pending`, `approved`, and `rejected`.
   Connect these hooks to your telemetry pipeline to keep review
   dashboards in sync with the new database-backed workflow.
