# AI Job Matcher

A college-ready full-stack app that ranks demo jobs against a candidate profile or PDF resume.

## Stack
React + Vite, FastAPI, SQLite, PyMuPDF, scikit-learn. Hybrid score = 60% required-skill overlap + 40% text similarity. Optional sentence embeddings can be enabled by installing `pip install -r requirements-semantic.txt` from the `backend` folder and setting `USE_SENTENCE_TRANSFORMERS=true`; this downloads a model and uses more memory, so it is not recommended for a small free instance.

## Run locally
Requirements: Python 3.11+ and Node.js 20+.

Backend terminal:
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Frontend terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. API docs: http://127.0.0.1:8000/docs.

## Test
From `backend` with the virtual environment active: `pytest -q`

## Deploy to Render
Push this repository to GitHub, then create a Render Web Service connected to it. Use:
- Build command: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`
- Start command: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
- Environment variable: `USE_SENTENCE_TRANSFORMERS=false`

The FastAPI service serves the built React app and API from one origin. Demo jobs are seeded into SQLite automatically. SQLite on a free/ephemeral instance can reset after redeploy/restart. For persistent production data, use a managed database.

## API
- `GET /api/health`
- `GET /api/jobs`
- `POST /api/match` multipart fields: `profile_text` and optional PDF `resume`

The sample job companies/listings are fictional demo data. Scores are similarity estimates, not hiring probabilities. Review and verify all recommendations yourself. Do not commit resumes, credentials, `.env`, virtual environments, `node_modules`, build output, or database files.
