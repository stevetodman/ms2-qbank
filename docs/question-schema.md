# MS2 QBank Question Schema

This document summarizes the structure, validation rules, and example payloads for question records. The authoritative JSON Schema lives at [`data/schema/question.schema.json`](../data/schema/question.schema.json) and is enforced by [`scripts/validate_questions.py`](../scripts/validate_questions.py).

## Top-Level Object

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `id` | string | ✓ | Must match the pattern `^q_[0-9a-f]{8}$` (e.g., `q_1a2b3c4d`). |
| `stem` | string | ✓ | Non-empty string containing the question prompt. |
| `choices` | array<object> | ✓ | At least two entries; each choice validated per the table below. |
| `answer` | string | ✓ | Single capital letter that must correspond to one of the choice labels. |
| `explanation` | object | ✓ | Must include a non-empty `summary` and per-choice `rationales`. |
| `metadata` | object | ✓ | Must contain subject/system/difficulty/status/keywords per enumerations. |
| `tags` | array<string> | optional | When present, every tag must be a non-empty string. Used for supplemental categorization. |

## Choice Objects (`choices[]`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `label` | string | ✓ | Exactly one uppercase letter (`A`–`Z`). Labels must be unique within a question. |
| `text` | string | ✓ | Non-empty string describing the answer option. |

## Explanation Object (`explanation`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `summary` | string | ✓ | Non-empty narrative explaining the correct answer. |
| `rationales` | array<object> | ✓ | Non-empty array with exactly one entry per choice label. |

### Rationale Objects (`explanation.rationales[]`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `choice` | string | ✓ | Uppercase letter referencing one of the question's choice labels. |
| `text` | string | ✓ | Non-empty explanation for why the option is correct or incorrect. |

## Metadata Object (`metadata`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `subject` | string | ✓ | One of: Anatomy, Behavioral Science, Biochemistry, Biostatistics, Immunology, Microbiology, Pathology, Pharmacology, Physiology. |
| `system` | string | ✓ | One of: Cardiovascular, Endocrine, Gastrointestinal, Hematologic/Lymphatic, Musculoskeletal, Nervous, Renal, Reproductive, Respiratory, Skin/Connective Tissue, Multisystem. |
| `difficulty` | string | ✓ | One of: Easy, Medium, Hard. |
| `status` | string | ✓ | One of: Unused, Marked, Incorrect, Correct, Omitted. |
| `keywords` | array<string> | ✓ | Non-empty list; each keyword must be a non-empty string. |
| `media` | array<object> | optional | When provided, each item must pass the media rules below. |
| `references` | array<object> | optional | When provided, each item must pass the reference rules below. |

### Media Objects (`metadata.media[]`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `type` | string | ✓ | One of: image, audio, video. |
| `uri` | string | ✓ | Non-empty string; should be a valid URI to the asset. |
| `alt_text` | string | ✓ | Non-empty accessible description of the asset. |

### Reference Objects (`metadata.references[]`)

| Field | Type | Required | Validation rules |
| --- | --- | --- | --- |
| `title` | string | ✓ | Non-empty citation title. |
| `source` | string | ✓ | Non-empty publication or resource name. |
| `url` | string | ✓ | Non-empty string; expected to be a resolvable URI. |

## Tag Categories

Tags allow downstream experiences (filters, analytics, recommendations) to group questions without modifying the enumerated metadata. Tags should map to one of the following categories:

| Category | Description | Example tags |
| --- | --- | --- |
| Emphasis | Highlights study prioritization or pedagogic intent. | `high-yield`, `foundational`, `advanced-review` |
| Clinical Focus | Identifies organ systems, disease clusters, or clinical themes beyond the `system` enum. | `vascular`, `autoimmune`, `oncology`, `infection` |
| Population | Flags demographic or patient context that influences presentation. | `pediatrics`, `geriatrics`, `obstetrics` |
| Modality | Indicates question formats, linked resources, or skill focus. | `imaging`, `pharmacology-table`, `calculation` |

When inventing new tags, select the category first and ensure the string is a concise, kebab-cased descriptor. Multiple tags from different categories can coexist on the same record to support compound filtering (e.g., `"tags": ["high-yield", "pediatrics", "infection"]`).

## Example Question

```json
{
  "id": "q_1a2b3c4d",
  "stem": "A 25-year-old man presents with chest pain and dyspnea after a long-haul flight. Which of the following is the most likely diagnosis?",
  "choices": [
    { "label": "A", "text": "Tension pneumothorax" },
    { "label": "B", "text": "Pulmonary embolism" },
    { "label": "C", "text": "Acute myocardial infarction" },
    { "label": "D", "text": "Pericarditis" }
  ],
  "answer": "B",
  "explanation": {
    "summary": "Prolonged immobilization increases the risk of deep vein thrombosis, which can embolize to the pulmonary circulation causing sudden dyspnea and pleuritic chest pain.",
    "rationales": [
      { "choice": "A", "text": "Tension pneumothorax typically presents with tracheal deviation and hyperresonance, which are absent here." },
      { "choice": "B", "text": "Pulmonary embolism matches the patient's risk factors and acute dyspnea after prolonged immobilization." },
      { "choice": "C", "text": "Acute MI often presents with crushing substernal chest pain and EKG changes." },
      { "choice": "D", "text": "Pericarditis causes sharp chest pain that improves when leaning forward." }
    ]
  },
  "metadata": {
    "subject": "Pathology",
    "system": "Respiratory",
    "difficulty": "Medium",
    "status": "Unused",
    "keywords": ["pulmonary embolism", "deep vein thrombosis", "risk factors"],
    "media": [
      {
        "type": "image",
        "uri": "https://example.com/images/pe_ct_scan.png",
        "alt_text": "CT angiogram demonstrating a pulmonary embolus"
      }
    ],
    "references": [
      {
        "title": "Pulmonary Embolism: Clinical Features",
        "source": "UWORLD Respiratory Module",
        "url": "https://example.com/references/pe"
      }
    ]
  },
  "tags": ["high-yield", "vascular"]
}
```

In this example, `high-yield` maps to the **Emphasis** category while `vascular` maps to **Clinical Focus**, enabling learners to filter for urgent review content related to vascular complications.

## Validation Workflow

To validate one or more data files locally:

```bash
python scripts/validate_questions.py data/questions/sample_questions.json
```

The script will enforce every rule described above and report detailed errors if a record violates the schema.
