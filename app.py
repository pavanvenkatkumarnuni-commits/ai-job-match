from contextlib import asynccontextmanager
from pathlib import Path

import fitz
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import get_jobs, init_db
from matcher import match_jobs
from features import router as features_router

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT_DIR / "dist"
MAX_RESUME_BYTES = 5 * 1024 * 1024
MAX_PROFILE_CHARS = 50_000

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI Job Matcher API", description="Hybrid resume-to-job matching and career planning tools.", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["*"],
)
app.include_router(features_router)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Job Matcher", "version": "2.0.0"}

@app.get("/api/jobs")
def list_jobs(
    role: str = Query(default="", max_length=120),
    skills: str = Query(default="", max_length=500),
    location: str = Query(default="", max_length=120),
    remote: bool = False,
    salary_min: int = Query(default=0, ge=0, le=1000000),
    salary_max: int = Query(default=1000000, ge=0, le=1000000),
):
    jobs = get_jobs()
    # Explicit demo salary bands are illustrative estimates, not live vacancy data.
    for job in jobs:
        title = job["title"].lower()
        if "machine learning" in title: low, high = 600000, 1400000
        elif "data analyst" in title: low, high = 350000, 800000
        elif "full stack" in title: low, high = 400000, 1000000
        elif "frontend" in title: low, high = 350000, 850000
        elif "qa" in title: low, high = 300000, 700000
        else: low, high = 350000, 900000
        job["salary_min"], job["salary_max"] = low, high
        job["work_mode"] = "Remote" if "remote" in job.get("location", "").lower() else ("Hybrid" if "hybrid" in job.get("location", "").lower() else "On-site")
    if role:
        jobs = [j for j in jobs if role.lower() in (j["title"] + " " + j["description"]).lower()]
    if location:
        jobs = [j for j in jobs if location.lower() in j.get("location", "").lower()]
    if remote:
        jobs = [j for j in jobs if j["work_mode"] == "Remote"]
    if skills:
        wanted = [s.strip().lower() for s in skills.split(",") if s.strip()]
        jobs = [j for j in jobs if all(any(s in skill.lower() for skill in j["skills"]) for s in wanted)]
    jobs = [j for j in jobs if j["salary_max"] >= salary_min and j["salary_min"] <= salary_max]
    return jobs

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
    return {"candidate_skills": sorted({skill for job in matches for skill in job["matched_skills"]}), "total_jobs": len(matches), "matches": matches}

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found.")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
