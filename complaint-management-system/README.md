# AI-Powered Customer Complaint Management System

An AI-copilot-driven Customer Complaint Management module for pharmaceutical
API/FDF manufacturers. The AI is the primary interface — natural language and
document uploads are extracted into a structured complaint record, which the
AI populates, risk-assesses, and keeps in sync as the conversation continues.
The complaint form is the **output** of the AI, never manually edited.

## Why this exists (QMS context)

In a pharmaceutical Quality Management System, the Customer Complaint module
is usually the first signal that something went wrong after a product left
the manufacturing site. Its job is to capture the complaint in a structured,
traceable way, assess patient/product risk, and flag it for investigation —
distinguishing an isolated incident from a batch-wide quality trend. This
system automates the intake and initial risk-triage stage of that process,
deliberately scoped away from root-cause/CAPA determination and formal
regulatory reporting pathways, which require domain expertise beyond what an
LLM can responsibly assert on its own.

---

## Tech stack

| Layer                            | Technology                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| Frontend                         | React + Redux Toolkit (state management), Vite                                                      |
| Backend                          | Python, FastAPI                                                                                     |
| AI orchestration                 | LangGraph                                                                                           |
| LLM                              | Groq — `llama-3.1-8b-instant` (extraction/completeness), `llama-3.3-70b-versatile` (risk reasoning) |
| Database                         | PostgreSQL (via SQLAlchemy)                                                                         |
| Embeddings (duplicate detection) | Local `sentence-transformers` (`all-MiniLM-L6-v2`) — Groq has no embeddings endpoint                |
| Font                             | Google Inter                                                                                        |

### Note on the Groq model choice

The assignment brief specified `gemma2-9b-it`. Groq deprecated that model on
**August 8, 2025**, before this build — using it returns a `400
model_decommissioned` error. Groq's documented replacement,
`llama-3.1-8b-instant`, is used instead (same speed/latency class, better
price-performance). See `console.groq.com/docs/deprecations`.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally (or accessible remotely)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) binary installed (required by `pytesseract` for image uploads — not installed via pip)
- A Groq API key: [console.groq.com/keys](https://console.groq.com/keys)

### 1. Database

Create the database (tables are created automatically on app startup):

```bash
psql -U postgres -c "CREATE DATABASE complaint_db;"
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# then edit .env: set GROQ_API_KEY and your actual Postgres password in DATABASE_URL

uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Architecture

```
User → React (Redux) → FastAPI routers → LangGraph workflow → Groq LLM
                                              ↓
                                    PostgreSQL (complaint + audit log)
```

**LangGraph pipeline** (`graph_workflow.py`):

```
classify_input → extract → merge_state → completeness_check
→ duplicate_check → risk_assessment → END
```

Each node is a single-responsibility function in `graph_nodes.py`. Nodes never
touch the database directly — `routers_chat.py` loads state before invoking
the graph and persists the result after, keeping the graph pure and testable.

---

## Features implemented

**Core (per assignment spec):**

- AI Copilot as the sole input method — natural language and document upload
- Structured extraction into a Pydantic complaint schema
- AI risk assessment against an explicit, editable rubric (High/Medium/Low),
  with per-field reasoning (product impact, patient impact, investigation
  priority) rather than a single free-text blob
- Natural-language editing with per-field diff tracking — every AI edit shows
  old value → new value and whether it was user-stated or AI-inferred
- Document upload (PDF, email `.eml`, images via OCR, `.txt`)
- Full audit log of every field change, independent of the complaint record itself

**Additional AI features (beyond spec):**

- **Change-aware risk re-assessment** — when a field is edited, the AI
  explicitly evaluates whether the change is risk-relevant before deciding to
  re-run a full risk assessment, and the UI shows "Updated this turn" vs
  "Unchanged" accordingly. This also skips the risk LLM call entirely for
  non-risk-relevant edits (e.g. a customer name correction), which is both a
  cost/latency optimization and the most direct evidence that the system is
  reasoning about _what_ changed, not just re-running from scratch.
- **Completeness checker** — flags missing required fields conversationally,
  independent of risk assessment
- **Duplicate complaint detection** — embedding-based similarity (local
  `sentence-transformers` model) plus an exact batch-number check, surfaced as
  a dismissible flag for human review — never auto-merges or blocks saving
- **Suggested next-step categories** — the risk panel offers 2-4 possible
  investigation categories (e.g. "retest batch samples," "review equipment
  calibration logs"). This is deliberately _not_ root-cause or CAPA
  determination — see Scope below — and carries an explicit UI disclaimer

---

## Deliberately out of scope

These were considered and intentionally not built, since they require
domain-specific grounding beyond what an LLM can responsibly assert, or fall
outside the assignment's timeline:

- **Definitive root-cause / CAPA determination** — real root-cause analysis
  needs manufacturing/process expertise (equipment history, raw material
  records, environmental monitoring data) that isn't available to this
  system. What's built instead is a hedged, disclaimer-carrying list of
  investigation _categories_, not a diagnosis.
- **21 CFR Part 11 / e-signature compliance** — electronic records/signature
  requirements for regulated pharma systems
- **Adverse event / pharmacovigilance regulatory reporting** (MedWatch,
  EudraVigilance) — the schema includes an `adverse_event` category so the AI
  _can_ flag it, but no regulatory reporting pathway is implemented
- **PII/PHI governance** — no data retention policy, anonymization, or
  access-control tiering beyond a single implicit user
- **Production-grade OCR** — per assignment note, simple `pytesseract`
  extraction is used; scanned PDFs with no embedded text layer are not
  OCR'd (the user is prompted to upload an image instead, which is OCR'd)
- **Prompt-injection hardening on uploaded documents** — a known risk with
  LLM-processed file uploads, not mitigated in this build

## Known limitations

- **Storage model**: complaints are stored as a single JSON blob per row
  rather than a fully normalized relational schema. This keeps the build
  simple since no cross-field SQL querying is needed at this scale, but it
  won't scale to complex reporting queries without a schema redesign.
- **Duplicate detection is a flag, not a decision** — it never merges,
  deletes, or blocks a save; a human always makes the final call.
- **`.eml` only for email**, not Outlook's proprietary `.msg` format.
- **No authentication/authorization** — single implicit user throughout.

---

## Project structure

```
complaint-management-system/
├── backend/         # FastAPI + LangGraph + Groq
└── frontend/         # React + Redux + Vite
```

See `file_structure.md` for the full file-by-file breakdown.
