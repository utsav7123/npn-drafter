# Quick Start (5 Minutes)

## Option 1: Docker (Recommended)

```bash
# 1. Clone
git clone https://github.com/[your-username]/npn-drafter.git
cd npn-drafter

# 2. Configure
cp .env.example .env
# ⚠️ Edit .env and add your ANTHROPIC_API_KEY

# 3. Run
docker-compose up

# 4. Open browser
# → http://localhost:5000
```

Done. Try the sample products.

---

## Option 2: Local Python

```bash
# 1. Install Python 3.11+

# 2. Setup venv
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# ⚠️ Edit .env and add ANTHROPIC_API_KEY

# 5. Run
python app.py

# 6. Open browser
# → http://localhost:5000
```

---

## Option 3: Run Tests (No API Key Needed)

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Try the UI

1. Open http://localhost:5000
2. Click "Sample: Vitamin D (Class 1)"
3. Click "Generate Application Draft"
4. Review results:
   - **Classification**: Class 1, matched monographs
   - **Draft**: Structured application
   - **Validation**: Any issues found
   - **Checklist**: Human review items

---

## Troubleshooting

**"Error: ANTHROPIC_API_KEY not set"**
→ Edit `.env` and add your key: `ANTHROPIC_API_KEY=sk-ant-...`

**"Docker: command not found"**
→ Install Docker: https://docs.docker.com/get-docker/

**"Python 3.11: command not found"**
→ Install Python 3.11+: https://www.python.org/downloads/

**"Port 5000 already in use"**
→ Change port in `docker-compose.yml` or `app.py`

---

## Next: Understand the Design

After you get it running:

1. Read [README.md](README.md) (overview and design decisions)
2. Read [docs/architecture.md](docs/architecture.md) (component details)
3. Read [docs/what_next.md](docs/what_next.md) (production roadmap)
4. Review [tests/](tests/) (see how validation works)

---

**Questions?** Check [README.md](README.md) for full documentation.
