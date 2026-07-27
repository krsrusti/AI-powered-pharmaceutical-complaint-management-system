# Complaint Management System

A full-stack complaint intake and triage application. Users describe a complaint
through a chat interface; a LangGraph-orchestrated backend extracts structured
fields, checks completeness, screens for duplicates, and assesses risk using
Groq-hosted LLMs.

## Stack

- **Backend:** FastAPI, SQLAlchemy, LangGraph
- **Database:** PostgreSQL (via SQLAlchemy; MySQL-compatible connection strings
  also work — `database.py` is driver-agnostic)
- **LLM:** Groq
  - `gemma2-9b-it` — fast extraction and completeness checks (default)
  - `llama-3.3-70b-versatile` — risk assessment reasoning (configurable)
- **Frontend:** React + Vite, Redux Toolkit for state management
- **Font:** Google Inter

## Project Structure

```
complaint-management-system/
├── backend/
│   ├── main.py                # FastAPI app entrypoint
│   ├── config.py              # Environment/config settings
│   ├── schemas.py              # Pydantic models
│   ├── database.py            # SQLAlchemy models & session
│   ├── llm_client.py          # Groq client wrapper
│   ├── document_parser.py     # PDF/DOCX/TXT parsing
│   ├── prompts.py             # LLM prompt templates
│   ├── graph_state.py         # LangGraph state definition
│   ├── graph_nodes.py         # LangGraph node functions
│   ├── graph_workflow.py      # LangGraph workflow assembly
│   ├── duplicate_detector.py  # Duplicate detection logic
│   ├── routers_chat.py        # Chat endpoints
│   ├── routers_complaints.py  # Complaint CRUD endpoints
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── index.css
│       ├── store/
│       │   ├── store.js
│       │   ├── complaintSlice.js
│       │   └── chatSlice.js
│       └── components/
│           ├── ChatPanel.jsx
│           ├── ComplaintForm.jsx
│           ├── RiskPanel.jsx
│           ├── CompletenessAlert.jsx
│           └── DuplicateAlert.jsx
│
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in DATABASE_URL and GROQ_API_KEY
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`, with health check at
`GET /api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and proxies `/api`
requests to the backend.

## How It Works

1. A user describes their complaint in the chat panel.
2. The backend's LangGraph workflow:
   - Extracts structured fields (title, description, category, contact info)
     using the fast Groq model.
   - Checks completeness and asks follow-up questions if information is
     missing.
   - Once complete, checks for likely duplicate complaints already on file.
   - Assesses risk level (low/medium/high/critical) using the larger
     reasoning model.
3. The frontend displays completeness alerts, duplicate warnings, and the
   risk assessment alongside an editable complaint form, all backed by Redux
   state.

## Notes

- `database.py` uses a standard SQLAlchemy connection string, so swapping
  between PostgreSQL and MySQL only requires changing `DATABASE_URL`.
- Model names are configurable via environment variables (`GROQ_FAST_MODEL`,
  `GROQ_REASONING_MODEL`) without code changes.
