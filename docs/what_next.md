# What's Next: Production Roadmap

## Current State (POC)

This prototype demonstrates:
- ✓ Rules-based classification (Class 1/2/3)
- ✓ Simple monograph retrieval
- ✓ LLM-assisted application drafting
- ✓ Hard-constraint validation
- ✓ Human review checklist generation
- ✓ Web UI for demos

## What's Missing for Production

### 1. Real Monograph Database

**Current**: 5 hand-built monograph JSON files

**Needed**:
- All 1,000+ Health Canada NNHPD monographs
- Integration with Health Canada's official monograph list
- Automated monograph updates (when Health Canada publishes changes)
- Version tracking (so old applications can be reproduced)

**Implementation**:
- Use a vector database (Chroma, FAISS, Weaviate, or pgvector)
- Scrape/ingest the official NNHPD corpus
- Set up a cron job to sync with Health Canada updates
- Store monograph versions with timestamps

### 2. Class 2 & 3 Handling

**Current**: Classifier identifies Class 2/3, but the system doesn't help draft them

**Needed**:
- Multi-monograph reconciliation logic (when ingredients are in different monographs, find overlapping claims)
- Class 3 evidence retrieval from PubMed, regulatory databases, supplier documentation
- Dosing advice for novel combinations
- Interaction checker (warn if ingredients may interact)

**Implementation**:
- For Class 2: LLM reconciliation of claims across monographs
- For Class 3: PubMed API integration, manual evidence templates
- Build a small ontology of known ingredient interactions

### 3. Audit & Compliance

**Current**: No audit log

**Needed**:
- Every LLM call logged (prompt, response, timestamp, user)
- Every validation decision logged
- Ability to "replay" an application 6 months later and get identical results
- Export audit trail for regulatory review

**Implementation**:
- PostgreSQL audit table
- Prompt version control (git or versioning system)
- Store monograph versions at time of application
- Deterministic LLM calls (use temperature=0, seed parameter)

### 4. Supplier & CoA Integration

**Current**: Application draft, but no verification

**Needed**:
- Upload certificates of analysis (CoA) from suppliers
- Validate ingredient identity, purity, microbial limits
- Track batch numbers and expiry dates
- Link CoA to the monograph requirements

**Implementation**:
- S3 or similar file storage for CoA documents
- OCR or manual field extraction from CoA
- Checklist in validator: "CoA on file? Purity ≥ X%? Microbial limits OK?"

### 5. Real PLA Form Integration

**Current**: Structured JSON output

**Needed**:
- Generate actual PLA PDF form (or fillable form) that Health Canada accepts
- Integrate with Health Canada's web submission portal
- Validate form completeness before submission
- Handle form updates (Health Canada changes the form periodically)

**Implementation**:
- Use reportlab or similar to generate PDF
- Parse Health Canada's form schema/XSD
- Build form generator that maps application data → form fields
- Test against sample forms from Health Canada

### 6. User Authentication & RBAC

**Current**: No auth

**Needed**:
- User accounts (company + individuals)
- Role-based access control:
  - Product Manager (create/edit applications)
  - Regulatory Affairs (review & submit)
  - Admin (manage company account)
- Per-company isolation (company A cannot see company B's drafts)

**Implementation**:
- Auth0, Keycloak, or simple JWT
- Database of users and role assignments
- Row-level security in database

### 7. Evaluation Framework

**Current**: No ground truth

**Needed**:
- Collect known good applications (public approvals from Health Canada)
- Use as regression tests
- Track accuracy: does the system output match the approved application?
- Continuously improve prompts based on failures

**Implementation**:
- NNHPD database of approved products is public
- Scrape ~100 approved applications with metadata
- Build evaluation pipeline that compares system output to approved version
- Track metrics: claim matching accuracy, dose correctness, classification accuracy

### 8. LLM Fallbacks & Robustness

**Current**: Falls back to template if Claude unavailable

**Needed**:
- Multiple LLM providers (Claude, GPT-4, Gemini)
- Graceful fallback when API quota exceeded
- Retry logic with exponential backoff
- Cost optimization (smaller model for simple tasks, larger for complex)

**Implementation**:
- Provider abstraction layer (interface that multiple LLMs implement)
- Fallback chain: Claude → GPT-4 → local model
- Cost tracking per API call
- Rate limiting and quota management

### 9. Monograph Confidence & Licensing

**Current**: Assumes all monographs are equally applicable

**Needed**:
- Confidence scores from classifier (is the ingredient match really this monograph?)
- Note license/patent considerations (some ingredients have restrictions)
- Link to official monograph URL (so applicant can double-check)
- Track monograph deprecation (Health Canada retires old monographs)

**Implementation**:
- Confidence scores in classifier output (e.g., 0.95 = very sure, 0.6 = ambiguous)
- Metadata per monograph: license, restrictions, deprecation date
- User notification if monograph is outdated or deprecated

### 10. Testing & Validation

**Current**: Basic pytest coverage

**Needed**:
- Integration tests with real Health Canada forms
- Load testing (can the system handle 100 simultaneous drafts?)
- Security testing (SQL injection, prompt injection, XSS)
- Regression tests on ground truth applications
- Performance benchmarks

**Implementation**:
- pytest with fixtures for common scenarios
- Locust for load testing
- OWASP security scanning
- Benchmark suite (time to classify, draft, validate)

## Production Deployment Checklist

- [ ] Real NNHPD monograph corpus ingested
- [ ] Vector database running
- [ ] Audit logging enabled
- [ ] User authentication enabled
- [ ] PLA form generation working
- [ ] CoA upload & validation working
- [ ] All integration tests passing
- [ ] Security scan passed (OWASP)
- [ ] Load testing passed (100+ concurrent users)
- [ ] Documentation complete (user manual, API docs, admin guide)
- [ ] Health Canada consultation (ensure compliance before production)
- [ ] Disaster recovery plan (backup, restore, audit trail recovery)

## Timeline Estimate (Professional Team)

- **Phase 1** (Weeks 1-2): Monograph ingestion, vector DB
- **Phase 2** (Weeks 3-4): Class 2/3 logic, evidence retrieval
- **Phase 3** (Weeks 5-6): Audit logging, supplier integration
- **Phase 4** (Weeks 7-8): PLA form generation, real form integration
- **Phase 5** (Weeks 9-10): Authentication, RBAC, multi-tenancy
- **Phase 6** (Weeks 11-12): Testing, security, load testing, documentation

**Total: ~3 months for a production-ready system.**

## Why This POC Matters

This proof of concept demonstrates:

1. **Architectural soundness**: Rules + validation + human review is a defensible design.
2. **Regulatory awareness**: The validation layer and audit trail show you understand compliance.
3. **Scalability thinking**: The design scales to Class 2/3 and beyond with the additions listed above.
4. **Team capability**: Building this system showcases full-stack development, AI integration, regulatory knowledge, and systems thinking.

A hiring manager at a regulatory-adjacent startup (like Organika) sees this POC and thinks: *"This person not only knows how to build systems, they understand the regulatory context and can extend the design to production."*
