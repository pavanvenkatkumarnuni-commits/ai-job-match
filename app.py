from contextlib import asynccontextmanager
from pathlib import Path

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import get_jobs, init_db
from matcher import match_jobs

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
MAX_RESUME_BYTES = 5 * 1024 * 1024
MAX_PROFILE_CHARS = 50_000

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI Job Matcher API", description="Hybrid resume-to-job matching for a college project.", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Job Matcher"}

@app.get("/api/jobs")
def list_jobs():
    return get_jobs()

@app.post("/api/match")
async def find_matches(profile_text: str = Form(default=""), resume: UploadFile | None = File(default=None)):
    text = profile_text.strip()
    if resume is not None:
        if resume.content_type != "application/pdf" and not (resume.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Please upload a PDF resume.")
        contents = await resume.read()
        if len(contents) > MAX_RESUME_BYTES:
            raise HTTPException(status_code=413, detail="Resume must be 5 MB or smaller.")
        try:
            with fitz.open(stream=contents, filetype="pdf") as document:
                extracted = "\n".join(page.get_text() for page in document)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Unable to read this PDF. Upload a valid, text-based PDF.") from exc
        text = (text + "\n" + extracted).strip()
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Enter at least 10 characters of profile text or upload a resume.")
    if len(text) > MAX_PROFILE_CHARS:
        raise HTTPException(status_code=400, detail="Profile text must be 50,000 characters or fewer.")
    try:
        matches = match_jobs(text, get_jobs())
    except Exception as exc:
        print(f"Matching error: {exc}")
        raise HTTPException(status_code=503, detail="Matching failed. Check server logs and model configuration.") from exc
    return {
        "candidate_skills": sorted({skill for job in matches for skill in job["matched_skills"]}),
        "total_jobs": len(matches),
        "matches": matches,
    }

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
