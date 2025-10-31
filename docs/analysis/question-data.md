# Question Data Audit

## Overview
The `data/questions/` directory has been restored with representative sample records that exercise the expected structure,
metadata coverage, and tagging conventions. These exemplars unblock downstream tooling while production-scale datasets are being
prepared for import.

## Data Snapshot
- `data/questions/sample_questions.json` – array of high-fidelity multiple-choice questions.
- `data/schema/question.schema.json` – JSON Schema describing the contract enforced across all question payloads.

The sample records intentionally include rich metadata (keywords, references, media attachments, and tags) to demonstrate how
features such as adaptive practice, content linking, and analytics can consume the fields.

## Schema Reference
The authoritative schema now lives alongside the data at `data/schema/question.schema.json`. It specifies:
- Required top-level fields (`id`, `stem`, `choices`, `answer`, `explanation`, `metadata`).
- Enumerations for `subject`, `system`, `difficulty`, and `status` aligned with the product requirements in `README.md`.
- Nested object structures for choices, explanations, media assets, and references.

Any evolution of the data contract should happen within that file so that automated validators and data producers remain in sync.

## Validation Workflow
A lightweight validation helper is available to confirm schema compliance and metadata coverage:

```bash
python scripts/validate_questions.py
```

The script scans every JSON artifact under `data/questions`, enforces enumerated vocabularies, verifies that answers match
existing choice labels, and ensures keywords and explanations are populated. It returns a non-zero exit code when any record
fails validation, making it suitable for local pre-commit hooks or CI pipelines.

## Downstream Impact
- **Developer experience:** Contributors can now inspect realistic records, iterating on features like filtering, analytics, and
  review flows without waiting for the full production dataset.
- **Automation readiness:** The shared schema and validator establish an executable contract that prevents regressions in
  metadata coverage or field naming.
- **Future extensibility:** By colocating schema, data, and validation scripts, future imports can plug into the same workflow
  while adding richer media, reference links, or tagging dimensions.

## Next Steps
- Expand the dataset with real or anonymized questions exported from the content pipeline.
- Integrate `scripts/validate_questions.py` into CI (e.g., GitHub Actions) to block malformed payloads automatically.
- Extend the validator with additional domain-specific rules such as difficulty calibration ranges or duplicate stem detection.
