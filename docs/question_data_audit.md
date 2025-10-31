# Question Bank Data Audit

## Dataset Overview
- **Location:** `data/questions/`
- **Files Reviewed:** `sample_questions.json`
- **Record Count:** 2 questions.

## Schema Summary
- `id` *(string)*: Unique identifier for the question. Present for all records.
- `stem` *(string)*: Question prompt text. Present for all records.
- `choices` *(array of objects)*: Answer options. Each choice contains:
  - `label` *(string)*: Choice identifier (e.g., "A").
  - `text` *(string)*: Option text.
- `answer` *(string)*: Label of the correct choice.
- `explanation` *(object)*:
  - `summary` *(string)*: High-level explanation. Present for all records.
  - `rationales` *(array of objects)*: Choice-specific rationales. Fields:
    - `choice` *(string)*: Choice label referenced.
    - `text` *(string)*: Rationale content.
- `metadata` *(object)*:
  - `subject` *(string)*
  - `system` *(string)*
  - `difficulty` *(string)*
  - `status` *(string)*
  - `keywords` *(array of strings)*
  - `media` *(array of objects, optional)*:
    - `type` *(string)*
    - `uri` *(string)*
    - `alt_text` *(string)*
  - `references` *(array of objects, optional)*:
    - `title` *(string)*
    - `source` *(string)*
    - `url` *(string)*
- `tags` *(array of strings)*: Thematic labels for search/filtering.

## Required Fields
Based on current data and validation rules, the following fields are required for question integrity:
- `id`, `stem`, `choices`, `answer`, `explanation.summary`, `explanation.rationales`, `metadata.subject`, `metadata.system`, `metadata.difficulty`, `metadata.status`, and `tags`.
- Each `choices` entry must have a matching `explanation.rationales` entry keyed by the same choice label.
- When `metadata.media` is provided, each object must include `type`, `uri`, and `alt_text`.
- When `metadata.references` is provided, each object must include `title`, `source`, and `url`.

## Observed Inconsistencies & Gaps
- **Media coverage:** Only one record currently provides `media`. Clarify whether rich media support is optional or required for specific question types so the dataset can be expanded consistently.
- **Reference depth:** References are now complete, but continue monitoring for multiple sources where appropriate to strengthen traceability.

## Recommendations
1. Mandatory metadata requirements are now documented above, including explicit `media` and `references` field expectations.
2. Validation enforces a 1:1 relationship between `choices` and `explanation.rationales` entries to guarantee rationale coverage.
3. `references` now require `url` values to improve source transparency across the dataset.

## Automated Validation Workflow
- `scripts/validate_questions.py` now lints every JSON file in `data/questions/` concurrently and surfaces a summarized error report grouped by file, enabling faster triage when the dataset grows.
- The GitHub Actions workflow defined in `.github/workflows/validate.yml` installs project dependencies plus `jsonschema`, executes `python scripts/validate_questions.py`, and blocks merges when validation fails.
- Contributors can reproduce the checks locally with `python scripts/validate_questions.py`; the command reports the number of validated questions and highlights any failing files with detailed error listings.

