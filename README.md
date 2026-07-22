# Agentic Hiring Workflow 🚀🤖💼

Automated multi-agent system to streamline technical hiring pipelines: AI-driven job description (JD) generation, resume parsing & indexing, and candidate retrieval + reranking. Built as a lightweight FastAPI backend with a Streamlit UI to orchestrate LangGraph / LangChain-based LLM workflows, vector search (FAISS), and simple PDF/resume handling.

Key goals:
- Generate high-quality job descriptions from a short recruiter input.
- Accept resumes (PDF / DOCX / TXT), extract structured candidate profiles and store vector embeddings for retrieval.
- Retrieve and rerank top candidates for a JD using FAISS + cross-encoder reranking.
- Simple approval/rejection loop with human-in-the-loop feedback for JD revisions.

---

## Features
- AI Job Description generation (create, review, approve, regenerate with feedback).
- Resume pool ingestion and parsing (PDF/DOCX/TXT).
- Vector indexing (FAISS) and candidate retrieval with cross-encoder reranking.
- Lightweight API (FastAPI) with a Streamlit dashboard for end-to-end flows.
- Configurable via environment variables (.env).

---

## Stack
- Languages: Python (primary), HTML (small UI/templates)
- Frameworks: FastAPI (backend), Streamlit (dashboard)
- Notable libraries: langgraph / langchain / langsmith, pydantic (settings/models), faiss-cpu, sentence-transformers, pypdf / python-docx, uvicorn

See `requirements.txt` for full dependency list.

---

## Repository layout (top-level)
Use this as a dev orientation — files not listed here are small helpers or config.

```text
.
├── app/                       # Application package: FastAPI app, UI submodules, core config
│   ├── api/
│   │   └── main.py            # FastAPI app entrypoint (routes mounted from routers)
│   ├── core/
│   │   ├── settings.py        # pydantic-settings configuration & defaults
│   │   └── logger.py          # loguru logger setup
│   ├── ui/                    # Streamlit-based dashboard (app UI)
│   ├── graph/                 # LangGraph workflow definitions & nodes (or integration)
│   ├── prompts/               # Prompt templates for JD generation & nodes
│   ├── schemas/               # Pydantic schemas used by API & workflows
│   ├── services/              # PDF/email/embedding helper services
│   └── utils/                 # Utility helpers (logging, etc.)
├── streamlit_app.py           # Streamlit dashboard (root-level entry used in repo)
├── data/                      # persistent artifacts: jobs, resumes, outputs, vector store path
├── tests/                     # pytest tests
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variable file
└── README.md
```

How it fits together (runtime shape)
- The FastAPI app (`app.api.main`) mounts routers for jobs, resumes, and retrieval. It provides endpoints consumed by the Streamlit UI and other clients.
- The Streamlit app (`streamlit_app.py`) is a thin UI that calls the backend endpoints to create JDs, upload resumes, and run retrieval workflows.
- Workflows (LangGraph/LangChain) are implemented in the app/graph and prompts directories: they use the configured LLM provider and embeddings model, store embeddings in FAISS (local vector store), and persist job/resume metadata under `data/`.

---

## Quickstart — run locally

Prereqs
- Python 3.10+ (match your environment)
- git
- (Optional) A virtual environment tool (venv, conda)
- Some dependencies (faiss-cpu, sentence-transformers) can be heavy — install in an environment with sufficient memory.

1. Clone
```bash
git clone https://github.com/saket0x07/Agentic-Hiring-Workflow.git
cd Agentic-Hiring-Workflow
```

2. Create and populate .env
- Copy the example .env and add real API keys.
```bash
cp .env.example .env
# Edit .env to set your keys and configuration:
# - OPENROUTER_API_KEY or other LLM provider keys
# - MODEL_NAME (configured in app/core/settings.py as required)
# - DATABASE_URL (default: sqlite)
# - FAISS_INDEX_PATH (vector store)
```
Important environment variables (from `.env.example` and `app/core/settings.py`):
- OPENROUTER_API_KEY (required) and MODEL_NAME (required) — or other LLM keys per your chosen providers.
- DEFAULT_LLM_MODEL, TEMPERATURE — model tuning.
- LANGCHAIN_API_KEY / LANGCHAIN_PROJECT — optional for tracing/tracking.
- DATABASE_URL (default local sqlite).
- SMTP_* — only required if using email features.

3. Create virtual env & install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
Note: If `faiss-cpu` installation fails, follow platform-specific guidance from FAISS (or use a Conda environment).

4. Run the backend (FastAPI)
From repository root:
```bash
# recommended for development (reload enabled)
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```
The app exposes health and version endpoints:
- GET /             -> welcome message
- GET /health       -> health check (returns status and environment)
- GET /version      -> app name & version

The Streamlit UI (next step) expects the backend at http://127.0.0.1:8000 by default.

5. Run the Streamlit dashboard
```bash
streamlit run streamlit_app.py
```
Open the local Streamlit URL shown in your terminal (default http://localhost:8501).

---

## API (observed contract used by the dashboard)
The Streamlit UI uses the following endpoints — ensure your backend implements these routes (the repo mounts routers for jobs, resumes, retrieval):

- GET /jobs/  
  Returns list of job objects.

- POST /jobs/create  
  Create a new hiring request and trigger JD generation. Example JSON payload:
  ```json
  {
    "role": "Senior Backend Engineer",
    "department": "Engineering",
    "experience": "3-5 years",
    "location": "Remote",
    "employment_type": "full_time",
    "work_mode": "remote",
    "budget": "$120,000 - $150,000",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "preferred_skills": ["AWS", "Redis", "Kubernetes"],
    "notes": "Looking for someone with strong API design background."
  }
  ```

- GET /jobs/{job_id}  
  Fetch job record and current generated JD state (used for viewing and subsequent approval).

- POST /jobs/{job_id}/approve  
  Approve JD (backend should generate a PDF, update status to APPROVED and persist). Response expected: updated job.

- POST /jobs/{job_id}/reject  
  Send feedback to regenerate JD. Payload example: `{"feedback": "Include more AWS signal and system-design emphasis."}`

- POST /resumes/upload  
  Multipart upload endpoint to accept a file field (e.g., `file`), parse resume, create profile, compute embeddings and add to FAISS index. Response includes parsed profile and `resume_id`.

- POST /retrieval/{job_id}?top_k={k}  
  Run retrieval for given job_id and return ranked candidates:
  Response shape (example):
  ```json
  {
    "candidates": [
      {
        "resume_id": "resume-uuid",
        "similarity_score": 92.5,
        "rerank_score": 0.86,
        "profile": { "candidate_name": "...", "professional_summary": "...", "technical_skills": [...] }
      }
    ],
    "total_candidates": 12
  }
  ```

If you modify route names or payload schemas in the backend, update `streamlit_app.py` accordingly.

---

## Data & Persistence
- Default SQLite DB: `sqlite:///./database/hiring.db` (configurable via DATABASE_URL).
- Vector store (FAISS index) path configured via `FAISS_INDEX_PATH` in settings (default `./data/vector_store`).
- Job/resume artifacts placed under `data/` — adjust file paths & permissions as needed.

---

## Configuration (summary of important env vars)
Use `.env` (loaded by pydantic-settings in `app/core/settings.py`):
- OPENROUTER_API_KEY (or other LLM provider keys)
- MODEL_NAME (LLM model to use)
- DEFAULT_LLM_MODEL (fallback model)
- TEMPERATURE (LLM temperature)
- LANGCHAIN_API_KEY, LANGCHAIN_PROJECT (optional)
- DATABASE_URL
- FAISS_INDEX_PATH
- SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL — for email features
See `.env.example` for the full set of example entries.

---

## Development notes
- Logging uses `loguru` and writes to `logs/agentic_hiring.log`.
- Settings are cached via lru_cache; update .env and restart processes to pick up changes.
- The Streamlit app is intentionally thin — it posts to backend endpoints and expects the backend to perform heavy LLM / embedding work.
- Tests: `pytest` is included in dev dependencies. Run:
  ```bash
  pytest -q
  ```
- Lint & format:
  - black
  - flake8

---

## Troubleshooting & tips
- FAISS install: `faiss-cpu` can be tricky on some platforms. If pip install fails, prefer conda: `conda install -c pytorch faiss-cpu`.
- Memory: embedding models and sentence-transformers can be memory-intensive. Use smaller embedding models for local dev.
- LLM access: make sure the LLM API keys and model names are set correctly in `.env` especially `OPENROUTER_API_KEY` and `MODEL_NAME` (these are required in settings).
- If the Streamlit UI reports backend connection errors, verify:
  - Backend running at the URL configured in the sidebar (default http://127.0.0.1:8000)
  - CORS (if calling from a remote UI) and firewall
- Check logs in `logs/agentic_hiring.log` for detailed tracebacks.

---

## How to contribute
- Open issues for bugs or feature requests.
- Fork, create a feature branch, add tests and a clear PR description.
- Keep changes modular: separate UI, API, and graph/workflow changes.

---

## Next steps & suggestions
- Add an OpenAPI schema / docs for the jobs/resumes/retrieval routes (FastAPI provides /docs).
- Add a LICENSE file (MIT/Apache) to clarify usage.
- Add automated CI that runs linters and tests (e.g., GitHub Actions).
- Add example datasets in `data/` and a small seed script for local dev.

---

## Contact
Repository owner: saket0x07  
Open an issue or pull request in this repo for questions and improvements.
