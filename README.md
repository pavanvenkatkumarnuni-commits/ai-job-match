# AI Job Matcher — Career Toolkit

A full-stack career discovery demo built with React + Vite, FastAPI, SQLite, PyMuPDF, and scikit-learn.

## Features
- Hybrid resume/profile matching: 60% required-skill overlap + 40% TF-IDF text similarity.
- PDF resume upload and skill-gap explanations.
- Resume readiness checklist and optional job-description keyword alignment (heuristic, not an official ATS vendor score).
- Role-based learning roadmap with portfolio project ideas.
- Interview practice questions, sample answer frameworks, and a quiz.
- Built-in career chatbot for common resume, interview, learning, and job-search questions. It uses transparent local rules and does not call an external LLM.
- Demo job filters for role, skills, location, remote mode, and illustrative salary bands.
- Email/password accounts, signed sessions, saved jobs, profile-match history, and an application tracker.
- Compare up to three job matches side by side.

## Stack and repository layout
This repository keeps `app.py`, `features.py`, `database.py`, `matcher.py`, `App.jsx`, `App.css`, `index.html`, `index.css`, `main.jsx`, and `package.json` in the repository root. Vite builds to `dist/`; FastAPI serves that folder and the API from one Render web service.

## Run locally
Requirements: Python 3.11+ and Node.js 20+.

```bash
pip install -r requirements.txt
npm install
npm run build
uvicorn app:app --reload
```

For frontend hot reload in development, run `npm run dev` in another terminal and open the Vite URL.

## Render deployment
- Build command: `pip install -r requirements.txt && npm install && npm run build`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Environment variable: `USE_SENTENCE_TRANSFORMERS=false`
- **Required for account security:** set `APP_SECRET_KEY` to a long random secret in Render's Environment settings. Do not commit the secret to GitHub. Existing sessions are invalidated if this value changes.
- For data persistence across deploys/restarts, configure a persistent disk and set `DB_PATH` to a file path on that disk, or use a managed database. Without persistent storage, SQLite account data may be lost on a free/ephemeral instance.

## API
- `GET /api/health`
- `GET /api/jobs?role=&skills=&location=&remote=&salary_min=&salary_max=`
- `POST /api/match` multipart fields: `profile_text` and optional PDF `resume`
- `POST /api/resume/analyze` JSON: `profile_text`, optional `job_description`
- `POST /api/roadmap`, `POST /api/interview`, `POST /api/chat`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Authenticated: `GET /api/dashboard`, `POST /api/history`, `POST/DELETE /api/saved-jobs`, `POST/PATCH/DELETE /api/applications`

## Important limitations
- The included job listings and salary bands are fictional sample data, not live vacancies or verified compensation.
- Match/readiness/keyword scores are estimates and are not hiring probabilities or official ATS vendor scores.
- The chatbot uses local rule-based guidance; no external LLM API is configured.
- Resume text should be reviewed by the user. Do not upload sensitive information you do not want processed.
- For public production use, add rate limiting, email verification, password-reset flow, CSRF/session policy appropriate to the deployment, monitoring, backups, and a managed persistent database. Generate a strong unique `APP_SECRET_KEY`.
