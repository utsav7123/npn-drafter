# NPN Application Drafter – Proof of Concept

> A demonstration of AI-assisted Natural Health Product (NHP) application drafting for Health Canada regulatory submissions. **Not a production regulatory tool.**

## What This Is (In 30 Seconds)

This system takes a product specification (ingredients, intended use) and produces a structured draft for a Health Canada Natural and Non-prescription Health Product (NHP) application. It:

1. **Classifies** the product as Class 1, 2, or 3 based on ingredient coverage
2. **Matches** ingredients to Health Canada monographs
3. **Drafts** an application structure using AI
4. **Validates** the draft against regulatory rules (catches hallucinations)
5. **Generates** a human review checklist

## What It Is NOT

This is a **prototype**, not a regulatory submission tool. Critical clarifications:

- ❌ **Not a substitute for expert review.** All outputs require human regulatory approval.
- ❌ **Not official Health Canada guidance.** Consult the actual NNHPD for rules.
- ❌ **Monographs are simplified.** The 5 monograph files are hand-converted from public NNHPD data and are **outdated for production use**. Do not base real submissions on these files.
- ❌ **Not production-ready.** No audit logging, no supplier verification, no real form generation.
- ✓ **A proof of concept** that demonstrates understanding of the regulatory domain and AI system design.

## Try It Now

### With Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/[your-username]/npn-drafter.git
cd npn-drafter

# Copy environment template
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run with Docker
docker-compose up
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### Local Development

```bash
# Python 3.11+
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."  # or set in .env file

# Run Flask
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

### Run Tests

```bash
pytest tests/ -v
```

## How It Works

### The Pipeline

```
Product Spec (JSON) 
    ↓ [Classify: rules-based]
    → Matched monographs + Class 1/2/3
    ↓ [Retrieve: load monograph files]
    → Monograph data
    ↓ [Draft: LLM-assisted]
    → Structured application draft
    ↓ [Validate: hard rules]
    → Validation report (catches LLM errors)
    ↓ [Review: generate checklist]
    → Human reviewer checklist
    ↓
Structured Output (JSON)
```

### Design Choices & Why

#### 1. Rules-Based Classifier (Not LLM)

**Why?** 
- Deterministic: same input always produces same output
- Testable: easy to verify correctness
- Cheap: no API calls for typical products
- Transparent: you can see exactly why it classified as Class 1 vs. 2

LLM classifiers are tempting but produce different results on different days. For regulatory work, predictability matters more than sophistication.

**Tradeoff**: Cannot handle unusual ingredient names or novel combinations as gracefully as an LLM. Fallback: LLM is available for ambiguous cases.

#### 2. Validation After Drafting (Not During)

**Why?**
- LLMs hallucinate. They invent claims, make up ingredient sources, propose out-of-range doses.
- A separate validator layer catches these mistakes before a human sees them.
- The validator enforces hard rules: claims must be from the monograph list, doses must be within limits.

This is the key insight: **LLM + validator** is safer than **LLM alone**.

**Tradeoff**: Validation takes CPU time. For production, you'd cache validators for common rules.

#### 3. Separate Prompts (Not Hardcoded)

**Why?**
- Prompts are code. They deserve version control, testing, and review.
- Storing them in `prompts/` files makes them visible and auditable.
- Easy to iterate: tweak the prompt, commit, test, deploy.

**Tradeoff**: One more file to manage. Worth it for transparency.

#### 4. Human Review Checklist (Not Final Submission)

**Why?**
- Regulators care about accountability. A checklist shows you understand the review process.
- The checklist guides the human reviewer: "verify CoA, double-check claims, confirm dose limits."
- Future: automate some checks (e.g., CoA validation), but human review remains the gate.

**Tradeoff**: Still requires a regulatory expert. No AI can replace regulatory judgment.

### Architecture Deep Dive

For detailed component descriptions, see [docs/architecture.md](docs/architecture.md).

## Data Model

### Input: Product Spec (JSON)

```json
{
  "product_name": "Vitamin D3 Tablets",
  "medicinal_ingredients": [
    {
      "name": "Cholecalciferol",
      "source": "from lanolin",
      "dose": 1000,
      "unit": "IU"
    }
  ],
  "non_medicinal_ingredients": ["Microcrystalline cellulose"],
  "intended_use": "Supports bone and immune health"
}
```

### Output: Application Draft (JSON)

```json
{
  "product_name": "Vitamin D3 Tablets",
  "applicant_info": "...",
  "medicinal_ingredients": [
    {
      "ingredient": "Cholecalciferol",
      "source": "from lanolin",
      "dose": "1000 IU",
      "dose_numeric": 1000,
      "dose_unit": "IU",
      "monograph_reference": "vitamin_d"
    }
  ],
  "claims": ["Helps in the development and maintenance of bones and teeth."],
  "risk_information": {
    "cautions": ["Consult a health care practitioner if symptoms persist."],
    "contraindications": ["Do not use if hypersensitive to ingredients."],
    "known_adverse_reactions": []
  },
  "monograph_class": 1,
  "monographs_referenced": ["vitamin_d"]
}
```

### Validation Output

```json
{
  "valid": true,
  "total_issues": 0,
  "error_count": 0,
  "warning_count": 0,
  "issues": []
}
```

If validation fails:

```json
{
  "valid": false,
  "error_count": 2,
  "warning_count": 1,
  "issues": [
    {
      "severity": "ERROR",
      "field": "claims[1]",
      "message": "Claim not found in monograph allowed list: 'Cures cancer'"
    },
    {
      "severity": "ERROR",
      "field": "medicinal_ingredients[0].dose",
      "message": "Dose 10000 IU is above maximum 2500"
    },
    {
      "severity": "WARNING",
      "field": "non_medicinal_ingredients",
      "message": "Silica is not on the standard acceptable list"
    }
  ]
}
```

## Example Products

Three sample products are included to demonstrate Class 1, 2, and 3:

- **Class 1** (`samples/product_class1_simple.json`): Single ingredient (Vitamin D) → single monograph
- **Class 2** (`samples/product_class2_combo.json`): Multiple ingredients (Calcium + Vitamin D) → multiple monographs
- **Class 3** (`samples/product_class3_novel.json`): Novel extract (Ginseng + Curcumin) → no matching monographs → requires novel evidence

Load these via the web UI to see the system in action.

## Monograph Database

The system includes 5 hand-built monograph files (in `monographs/`):

1. `vitamin_d.json` – Vitamin D3
2. `calcium.json` – Calcium
3. `vitamin_c.json` – Vitamin C
4. `magnesium.json` – Magnesium
5. `multi_vitamin_mineral.json` – Multi-vitamin combinations

Each monograph contains:

```json
{
  "monograph_id": "vitamin_d",
  "name": "Vitamin D",
  "active_ingredient": "Cholecalciferol / Ergocalciferol",
  "dose_range": { "min_iu_per_day": 200, "max_iu_per_day": 2500 },
  "allowed_claims": [
    "Helps in the development and maintenance of bones and teeth.",
    "Supports immune system function."
  ],
  "duration_of_use": "Long-term use. Consult a health care practitioner if symptoms persist beyond 4 weeks.",
  "risk_information": { ... }
}
```

**Important**: These are simplified, hand-converted versions based on public NNHPD data. For real submissions, consult [Health Canada's official monograph library](https://www.canada.ca/en/health-canada/services/drugs-health-products/natural-non-prescription/applications-submissions/product-licensing/monographs.html).

## Running Tests

```bash
pytest tests/ -v
```

Tests cover:

- **Classifier**: Verify Class 1/2/3 logic with known products
- **Validator**: Feed invalid drafts, confirm errors are caught
- **Drafter**: Verify draft structure (uses template fallback to avoid LLM dependency)

Tests automatically run on every push (GitHub Actions).

## Project Structure

```
npn-drafter/
├── README.md                              # This file
├── requirements.txt                       # Python dependencies
├── docker-compose.yml                     # Docker orchestration
├── Dockerfile                             # Docker image definition
├── .env.example                           # Environment variables template
├── .gitignore                             # Git ignore rules
│
├── app.py                                 # Flask web server
│
├── agent/
│   ├── classifier.py                      # Class 1/2/3 determination
│   ├── retriever.py                       # Monograph lookup
│   ├── drafter.py                         # LLM-assisted drafting
│   ├── validator.py                       # Validation rules
│   └── reviewer_notes.py                  # Human review checklist
│
├── monographs/                            # Simplified Health Canada monographs
│   ├── vitamin_d.json
│   ├── calcium.json
│   ├── vitamin_c.json
│   ├── magnesium.json
│   └── multi_vitamin_mineral.json
│
├── prompts/                               # LLM prompts (version-controlled)
│   ├── classifier_prompt.txt
│   ├── drafter_prompt.txt
│   └── reviewer_prompt.txt
│
├── samples/                               # Example product specs for testing
│   ├── product_class1_simple.json
│   ├── product_class2_combo.json
│   └── product_class3_novel.json
│
├── templates/
│   └── index.html                         # Web UI
│
├── static/
│   └── style.css                          # Styling
│
├── tests/
│   ├── test_classifier.py                 # Classifier unit tests
│   ├── test_validator.py                  # Validator unit tests
│   └── test_drafter.py                    # Drafter tests
│
├── docs/
│   ├── architecture.md                    # System design deep dive
│   └── what_next.md                       # Production roadmap
│
└── .github/workflows/
    └── test.yml                           # CI/CD pipeline
```

## Requirements

- Python 3.11+
- Anthropic API key (for Claude)
- Docker & Docker Compose (optional, for containerized deployment)

See `requirements.txt` for Python dependencies.

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

Never commit `.env` (it's in `.gitignore`).

## What I Learned Building This

**Regulatory systems require hard constraints.** It's tempting to let an LLM drive everything ("just ask Claude!"). But regulators demand explainability and predictability. A rules-based validator is less sexy than a pure LLM system, but infinitely more defensible. For Organika and similar companies, this is the difference between a prototype and a production system.

**Prompts are code.** Treat them like version-controlled code artifacts. Test them. Review them. Track changes. This is how you catch prompt injection attacks and ensure reproducibility.

**The human review step is the feature, not the bottleneck.** Some people see human review as an obstacle to automate away. But in healthcare/regulatory contexts, human review is the whole point. The system's job is to make that review easier and more thorough, not to replace it.

## What's Missing (For Production)

This POC is intentionally minimal. A production system would add:

- ✓ Real NNHPD monograph corpus (1000+ monographs, vector-indexed)
- ✓ Class 2 & 3 support with evidence retrieval
- ✓ Audit logging (every decision traceable)
- ✓ Supplier CoA verification
- ✓ Real Health Canada PLA form generation
- ✓ Multi-tenant support (companies manage their own products)
- ✓ User authentication & role-based access
- ✓ Integration with Health Canada's web portal

See [docs/what_next.md](docs/what_next.md) for the full production roadmap.

## Why This POC Exists

This is an internship project for Organika Health Products. The goal is to demonstrate:

1. **Understanding of the regulatory domain** – NHP classification, monographs, Class 1/2/3, validation requirements.
2. **Systems thinking** – Modular architecture, clear separation of concerns, testable code.
3. **AI integration skills** – Prompt engineering, LLM fallbacks, validation layers, output parsing.
4. **Product intuition** – Honest about limitations, clear about what's missing, focused on the user (the regulatory reviewer).

## License

This is a proof-of-concept demo. Use freely for non-commercial purposes.

## Contact & Attribution

Built as part of an application to Organika Health Products.

- GitHub: [your-username/npn-drafter](https://github.com/[your-username]/npn-drafter)
- LinkedIn: [your profile](https://linkedin.com/in/[your-profile])

---

**Last Updated**: May 2024  
**Status**: Proof of Concept (POC)  
**Maintainer**: [Your Name]

---

## Quick Start Checklist

- [ ] Clone the repo
- [ ] Copy `.env.example` to `.env` and add your Anthropic API key
- [ ] Run `docker-compose up`
- [ ] Open [http://localhost:5000](http://localhost:5000)
- [ ] Load a sample product (Class 1, 2, or 3)
- [ ] Review the draft, validation report, and reviewer checklist
- [ ] Try editing the product spec to see how classification changes
- [ ] Run `pytest tests/ -v` to see validation in action
- [ ] Read [docs/architecture.md](docs/architecture.md) to understand the design
- [ ] Read [docs/what_next.md](docs/what_next.md) to see the production roadmap

---

### Disclaimer

⚠️ **This is a demonstration system, not a regulatory tool.**

- All outputs require expert human review.
- The monograph data is simplified and outdated.
- Do not use for actual Health Canada submissions without updating the monographs and obtaining regulatory approval.
- Consult Health Canada and a regulatory professional before submitting any NHP application.

This system is intended to showcase software architecture and regulatory knowledge, not to provide regulatory advice.
