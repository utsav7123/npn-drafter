# Architecture

## Overview

The NPN Application Drafter is a proof-of-concept system that demonstrates how AI can assist with Natural Health Product (NHP) regulatory applications for Health Canada.

## Design Principles

1. **Rules before LLM**: The classifier uses deterministic rules first, only calling the LLM for edge cases.
2. **Validation is non-negotiable**: The validator runs hard rules after LLM generation to catch hallucinations.
3. **Human review is permanent**: No amount of AI sophistication removes the need for expert regulatory review.
4. **Explainability**: Every decision is documented and traceable (classification reasoning, validator issues, reviewer checklist).

## Architecture Diagram

```
Product Spec (JSON)
      ↓
  ┌─────────────────┐
  │  Classifier     │  → Determines Class 1/2/3 using rules
  │  (rules + LLM)  │     Returns: matched monographs, reasoning
  └────────┬────────┘
           ↓
      ┌────────────────────┐
      │  Retriever         │  → Loads monograph JSON files
      │  (local DB)        │     Returns: monograph data for drafting
      └────────┬───────────┘
               ↓
        ┌──────────────────────┐
        │  Drafter (LLM)       │  → Uses Claude to fill application fields
        │  + Prompt Template   │     Returns: structured draft JSON
        └────────┬─────────────┘
                 ↓
          ┌─────────────────────┐
          │  Validator          │  → Runs hard rules:
          │  (rules-based)      │     - Dose ranges
          │                     │     - Claim matching
          │                     │     - Schema validation
          └────────┬────────────┘
                   ↓
            ┌──────────────────────┐
            │  Reviewer Notes      │  → Generates human checklist
            │  (template + LLM)    │     Returns: actionable items
            └──────────────────────┘
                   ↓
            Application Package
            (draft + validation + checklist)
                   ↓
            [HUMAN REVIEW & SUBMISSION]
```

## Component Breakdown

### 1. Classifier (`agent/classifier.py`)

**Input**: Product spec with ingredients and intended use

**Logic**:
- Iterate through medicinal ingredients
- Match each ingredient name to a monograph ID using a hand-built lookup table
- Count matched monographs:
  - 0 monographs found → Class 3
  - 1 monograph covers all ingredients → Class 1
  - Multiple monographs cover all ingredients → Class 2

**Output**: Classification with reasoning and matched monograph IDs

**Why this design?**
- Deterministic and testable (no randomness)
- Fast (no LLM call for typical products)
- Cheap (one rule lookup per ingredient)
- Can be extended to use an LLM as a fallback for ambiguous cases

### 2. Retriever (`agent/retriever.py`)

**Input**: List of monograph IDs

**Logic**:
- For each ID, load the JSON file from `monographs/` directory
- Return the full monograph data

**Output**: Dict mapping monograph_id → monograph data

**Why this design?**
- Simple, fast file-based lookup
- No dependencies on external services
- Production v2 would replace this with vector search over the real NNHPD corpus

### 3. Drafter (`agent/drafter.py`)

**Input**: Product spec + monograph data + API key

**Logic**:
1. Load drafter prompt template
2. Inject product spec and monographs into prompt
3. Call Claude API with structured JSON schema in prompt
4. Parse JSON response from LLM
5. Return structured draft

**Output**: Application draft JSON with fields like:
- `medicinal_ingredients`: array with ingredient, dose, source, monograph reference
- `claims`: array pulled from monograph
- `risk_information`: cautions and contraindications from monograph
- `monographs_referenced`: list of monograph IDs used

**Why this design?**
- Prompt is stored in a file (not hardcoded) for version control and auditability
- JSON schema in prompt helps the LLM produce structured output
- Fallback template exists if LLM fails

### 4. Validator (`agent/validator.py`)

**Input**: Application draft + monographs

**Checks**:
1. **Schema validation**: Is the JSON structure correct? (using jsonschema library)
2. **Dose range validation**: Are all doses within monograph limits?
3. **Claim validation**: Are all claims from the allowed monograph list?
4. **Required fields**: Are all necessary fields present?

**Output**: Validation report with:
- `valid`: bool
- `error_count`: number of critical issues
- `warning_count`: number of non-critical issues
- `issues`: list of {severity, field, message}

**Why this design?**
- Catches LLM hallucinations (invented claims, out-of-range doses)
- Deterministic rules (no ambiguity about what is/isn't allowed)
- Regulatory people understand this; it shows you take safety seriously
- Can be extended to check supplier certifications, batch testing, etc.

### 5. Reviewer Notes (`agent/reviewer_notes.py`)

**Input**: Application draft

**Logic**:
1. Load reviewer prompt
2. Call Claude to generate a checklist for human review
3. Fallback to a default checklist if LLM fails

**Output**: Checklist with items grouped by category:
- Ingredients (verify sources, CoA, suppliers)
- Doses (double-check against monograph)
- Claims (verify no unauthorized therapeutic claims)
- Labeling (check for safety warnings, directions for use)
- Subpopulations (doses for children, seniors, etc.)

**Why this design?**
- Makes the human review step explicit (not hidden in a document)
- Actionable items (the reviewer knows exactly what to check)
- Can be extended to link to regulatory guidance, previous approvals, etc.

### 6. Web UI (`app.py` + `templates/index.html`)

**Routes**:
- `GET /` : Serve form with textarea for JSON input
- `POST /api/draft` : Process spec through pipeline, return results
- `GET /api/sample-products` : Serve example product specs

**UI Features**:
- Tabbed results panel (Classification, Draft, Validation, Reviewer Checklist)
- Download draft as JSON
- Sample products for quick demo
- Responsive design

**Why this design?**
- No authentication needed for POC
- Plain HTML (no React, Vue, etc.) for minimal dependencies
- Flask is lightweight and easy to dockerize

## Data Flow

```
User Input (JSON)
      ↓
[Flask validates JSON structure]
      ↓
Classifier.classify_product()
      → Returns: class, matched_monographs, reasoning
      ↓
Retriever.get_monographs(matched_monographs)
      → Returns: monograph dict
      ↓
Drafter.draft_application(spec, monographs, api_key)
      → Calls Claude with prompt
      → Returns: application draft JSON
      ↓
Validator.validate_application(draft, monographs)
      → Checks schema, doses, claims, fields
      → Returns: validation report (errors/warnings)
      ↓
ReviewerNotes.generate_reviewer_notes(draft, api_key)
      → Calls Claude to generate checklist
      → Returns: checklist items grouped by category
      ↓
Combined Result (JSON)
      → classification
      → draft
      → validation
      → reviewer_notes
      ↓
[Return to user]
```

## Deployment

**Development**:
```bash
python -m flask run
```

**Docker** (recommended):
```bash
docker-compose up
```

## Testing Strategy

- **Classifier tests**: Verify Class 1/2/3 logic with known samples
- **Validator tests**: Feed invalid drafts, ensure errors are caught
- **Integration tests**: Full pipeline with mock LLM responses

Tests are in `tests/` and run via GitHub Actions on every push.

## Known Limitations & v2 Improvements

See [what_next.md](what_next.md)
