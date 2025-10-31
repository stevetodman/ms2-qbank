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
  - `references` *(array of objects)*:
    - `title` *(string)*
    - `source` *(string)*
    - `url` *(string, optional)*
- `tags` *(array of strings)*: Thematic labels for search/filtering.

## Required Fields
Based on current data, the following fields appear consistently populated and should be considered required for question integrity:
- `id`, `stem`, `choices`, `answer`, `explanation.summary`, `explanation.rationales`, `metadata.subject`, `metadata.system`, `metadata.difficulty`, `metadata.status`, and `tags`.

## Observed Inconsistencies & Gaps
- **Metadata references:** One record (`q_5e6f7a8b`) lacks `url` for the reference entry, suggesting the field is optional but may be expected for traceability.
- **Media coverage:** Only one record provides `media`. Clarify whether rich media support is optional or required for specific question types.
- **Rationale completeness:** All choices currently have rationales, but schema does not enforce 1:1 mapping between `choices` and `explanation.rationales`. Consider validation to ensure coverage.

## Recommendations
1. Define and document which metadata fields are mandatory, particularly for `references` and `media` entries.
2. Implement validation to enforce that every `choices` entry has a corresponding `explanation.rationales` entry.
3. Encourage inclusion of `url` within `references` to improve source transparency.

