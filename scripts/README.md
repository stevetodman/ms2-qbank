# Scripts Overview

## Question Dataset Migration & Validation
1. **Migrate the legacy export**
   ```bash
   python scripts/migrate_questions.py path/to/legacy_export.jsonl \
     --output-dir data/questions \
     --shard-size 250
   ```
   * Streams JSON arrays or JSON Lines exports without loading everything into memory.
   * Normalises legacy fields, fills metadata/tags, and writes sharded `questions_XXXX.json` files under `data/questions/`.

2. **Validate the regenerated shards**
   ```bash
   python scripts/validate_questions.py data/questions --workers 8
   ```
   * Parallelises schema validation and reports per-file error summaries for fast triage.

3. **Review the output**
   * Confirm shard counts reported by the migration script match expectations.
   * Ensure validation finishes with `ok` status for every shard before committing the data.
