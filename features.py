"""Local-first career tools and account-backed dashboard APIs."""
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api")
DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "jobs.db")))
SECRET = os.getenv("APP_SECRET_KEY", "development-only-change-this-before-production").encode()
SKILLS = ["Python","SQL","JavaScript","React","FastAPI","REST API","Machine Learning","scikit-learn","pandas","NumPy","Statistics","Excel","Data Visualization","Git","Docker","AWS","Java","C++","HTML","CSS","Testing","pytest","Linux","Communication","Problem Solving","Django","Flask","Power BI","API Testing"]
SKILL_RE = {s: re.compile(r"(?<![a-z0-9+#])"+re.escape(s.lower())+r"(?![a-z0-9+#])") for s in SKILLS}

def db():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS profile_history(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, profile TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS saved_jobs(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, job_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,job_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, job_title TEXT NOT NULL, company TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Saved', applied_date TEXT DEFAULT CURRENT_DATE, notes TEXT DEFAULT '')""")
    conn.commit()
    return conn

def token_for(user):
    payload=base64.urlsafe_b64encode(json.dumps({"uid":user["id"],"exp":int(time.time())+60*60*24*14}).encode()).decode().rstrip("=")
    sig=base64.urlsafe_b64encode(hmac.new(SECRET,payload.encode(),hashlib.sha256).digest()).decode().rstrip("=")
    return payload+"."+sig

def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401,"Sign in to use your personal dashboard.")
    token=authorization[7:]
    try:
        payload,sig=token.split(".",1)
        expected=base64.urlsafe_b64encode(hmac.new(SECRET,payload.encode(),hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(sig,expected): raise ValueError()
        data=json.loads(base64.urlsafe_b64decode(payload+"="*((4-len(payload)%4)%4)))
        if data["exp"] < time.time(): raise ValueError()
        with db() as conn: user=conn.execute("SELECT id,name,email FROM users WHERE id=?",(data["uid"],)).fetchone()
        if not user: raise ValueError()
        return dict(user)
    except Exception:
        raise HTTPException(401,"Session expired or invalid. Please sign in again.")

class AuthBody(BaseModel):
    name: str = Field(default="", max_length=80)
    email: str
    password: str = Field(min_length=8, max_length=128)
class ProfileBody(BaseModel):
    profile_text: str = Field(min_length=10, max_length=50000)
    job_description: str = Field(default="", max_length=20000)
class RoadmapBody(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    current_skills: list[str] = []
class InterviewBody(BaseModel):
    role: str = Field(min_length=2, max_length=120)
class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
class ApplicationBody(BaseModel):
    job_title: str = Field(min_length=1, max_length=160)
    company: str = Field(min_length=1, max_length=160)
    status: str = "Saved"
    applied_date: str = ""
    notes: str = Field(default="", max_length=2000)
class SavedBody(BaseModel):
    job_id: int

def skills_in(text):
    t=text.lower()
    return sorted([s for s,p in SKILL_RE.items() if p.search(t)])

@router.post("/auth/register")
def register(body: AuthBody):
    name=body.name.strip()
    email=body.email.strip().lower()
    if not name: raise HTTPException(400,"Please enter your name.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email): raise HTTPException(400,"Enter a valid email.")
    salt=secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac("sha256",body.password.encode(),bytes.fromhex(salt),240000).hex()
    try:
        with db() as conn:
            cur=conn.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(name,email,salt+":"+digest))
            user={"id":cur.lastrowid,"name":name,"email":email}
    except sqlite3.IntegrityError: raise HTTPException(409,"An account with this email already exists.")
    return {"token":token_for(user),"user":user}

@router.post("/auth/login")
def login(body: AuthBody):
    email=body.email.strip().lower()
    with db() as conn: row=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    if not row: raise HTTPException(401,"Email or password is incorrect.")
    salt,digest=row["password_hash"].split(":",1)
    check=hashlib.pbkdf2_hmac("sha256",body.password.encode(),bytes.fromhex(salt),240000).hex()
    if not hmac.compare_digest(check,digest): raise HTTPException(401,"Email or password is incorrect.")
    user={"id":row["id"],"name":row["name"],"email":row["email"]}
    return {"token":token_for(user),"user":user}

@router.get("/auth/me")
def me(user=Depends(current_user)): return {"user":user}

@router.post("/resume/analyze")
def analyze_resume(body: ProfileBody):
    text=body.profile_text.strip()
    found=skills_in(text)
    word_count=len(re.findall(r"\b[\w+#.-]+\b",text))
    sections={"Skills":bool(re.search(r"skills|technologies|technical",text,re.I)),"Projects":bool(re.search(r"projects?|built|developed|implemented",text,re.I)),"Experience":bool(re.search(r"experience|internship|employment",text,re.I)),"Education":bool(re.search(r"education|university|college|degree|b\.tech|bachelor",text,re.I))}
    suggestions=[]
    if word_count<80: suggestions.append("Add more detail: include measurable outcomes, project context, and responsibilities.")
    if not sections["Skills"]: suggestions.append("Add a clearly labelled Skills section with tools relevant to your target role.")
    if not sections["Projects"]: suggestions.append("Describe 2–3 projects using action verbs, technologies, and concrete results.")
    if not sections["Experience"]: suggestions.append("If you have experience or internships, add role, dates, contributions, and impact. Coursework can help if you are a fresher.")
    if not sections["Education"]: suggestions.append("Include your degree, institution, and expected graduation year.")
    if not re.search(r"\b(achieved|improved|reduced|increased|built|developed|automated|%|\d+)\b",text,re.I): suggestions.append("Quantify impact where truthful (e.g., records processed, latency reduced, or users supported).")
    score=min(100, max(15, 35+min(len(found)*4,36)+sum(sections.values())*5+(10 if word_count>=100 else 0)))
    job_text=body.job_description.strip()
    job_keywords=skills_in(job_text) if job_text else []
    matched_keywords=sorted(set(found) & set(job_keywords))
    missing_keywords=sorted(set(job_keywords) - set(found))
    ats_score=round(100*len(matched_keywords)/len(job_keywords)) if job_keywords else None
    if job_text and missing_keywords:
        suggestions.append("For the selected job description, consider adding truthful evidence for: "+", ".join(missing_keywords)+".")
    return {"resume_score":score,"ats_score":ats_score,"job_keywords":job_keywords,"matched_keywords":matched_keywords,"missing_keywords":missing_keywords,"word_count":word_count,"detected_skills":found,"sections":sections,"suggestions":suggestions,"disclaimer":"Heuristic feedback, not an official ATS score. Review for accuracy and tailor to each job."}

@router.post("/roadmap")
def roadmap(body: RoadmapBody):
    role=body.target_role.lower()
    current={x.lower() for x in body.current_skills}
    if any(k in role for k in ["data scientist","machine learning","ml engineer","ai"]):
        plan=[("Python and data foundations",["Python","SQL","Statistics","pandas","NumPy"],"Clean and explore a public dataset."),
              ("Machine learning",["Machine Learning","scikit-learn","Statistics"],"Train and evaluate a baseline classifier; explain precision, recall and limitations."),
              ("Model delivery",["FastAPI","Git","Docker"],"Expose the model through a tested REST API and document deployment.")]
    elif any(k in role for k in ["frontend","react","web"]):
        plan=[("Web fundamentals",["HTML","CSS","JavaScript"],"Build a responsive, accessible multi-page portfolio."),
              ("React applications",["React","REST API","Git"],"Build a searchable dashboard that consumes a public API."),
              ("Production quality",["Testing","Docker"],"Add component tests, error states, and a deployment pipeline.")]
    elif any(k in role for k in ["data analyst","analyst","business intelligence"]):
        plan=[("Query and clean data",["SQL","Excel","Python"],"Answer 10 business questions using a public dataset."),
              ("Analysis and statistics",["Statistics","pandas"],"Write a short exploratory analysis with clear assumptions."),
              ("Communicate insights",["Power BI","Data Visualization"],"Build a dashboard with 3 actionable findings.")]
    else:
        plan=[("Core programming",["Python","Git","SQL"],"Build a small CRUD application with version control."),
              ("Role-specific practice",["REST API","Testing","Problem Solving"],"Complete a project that demonstrates the top requirements in target job ads."),
              ("Portfolio and delivery",["Docker","Communication"],"Deploy the project, write a README, and prepare a 3-minute walkthrough.")]
    return {"target_role":body.target_role,"weeks":[{"week":i+1,"focus":title,"skills":[s for s in skills if s.lower() not in current],"project":project} for i,(title,skills,project) in enumerate(plan)],"note":"Suggestions are a starter plan. Compare them with current job descriptions and adjust to your time and background."}

@router.post("/interview")
def interview(body: InterviewBody):
    role=body.role.strip()
    return {"role":role,"questions":[
      {"question":f"Explain a project relevant to a {role} role.","sample_answer":"Use STAR: describe the problem, your specific contribution, the tools you chose, one challenge, and a measurable result. Be honest about what you personally built."},
      {"question":"Tell me about a technical problem you found difficult.","sample_answer":"Explain how you reproduced it, investigated possible causes, tested a fix, and verified the result. Mention what you would improve next time."},
      {"question":"How do you decide what to learn when a job requires an unfamiliar skill?","sample_answer":"Break the skill into fundamentals, build a small practical project, consult reliable documentation, and validate progress against the job requirements."},
      {"question":"How do you test the quality of your work?","sample_answer":"Describe relevant unit or integration tests, edge cases, review or debugging practices, and how you know the expected behavior is met."},
      {"question":f"What would you contribute in your first 30 days as a {role}?","sample_answer":"First learn the product, team workflow, and success criteria; then take a scoped task, seek feedback, and document what you learn."}
    ],"quiz":[{"question":"What is the strongest way to describe a project?","options":["List only the technologies","Explain problem, contribution, and outcome","Claim team work as individual work"],"answer":1},{"question":"If you do not know an interview answer, what should you do?","options":["Invent a confident answer","Explain your current understanding and how you would investigate","Stop speaking"],"answer":1}]}

@router.post("/chat")
def career_chat(body: ChatBody):
    q=body.message.lower()
    if any(x in q for x in ["resume","cv","ats"]):
        answer="Tailor your resume to the role: use relevant skills from the job description, show projects and measurable outcomes, keep headings clear, and never add skills you cannot discuss. Use the Resume Analyzer for a checklist."
    elif any(x in q for x in ["interview","question","viva"]):
        answer="Practice explaining one project end-to-end: the problem, your contribution, trade-offs, testing, and result. Use the Interview Prep section for starter questions and answer aloud with the STAR structure."
    elif any(x in q for x in ["roadmap","learn","study","skill"]):
        answer="Start from the target role's repeated requirements, pick one skill gap at a time, and build a small portfolio project that demonstrates it. The Learning Roadmap tab can generate a starter plan."
    elif any(x in q for x in ["job","career","role","salary","intern"]):
        answer="Compare several current job descriptions, note repeated required skills, and prioritize roles where you meet core requirements while having a realistic plan for gaps. The listings in this demo are fictional examples, not live vacancies."
    else:
        answer="I can help with resumes, skill gaps, learning plans, interview practice, and job-search strategy. Tell me your target role, current skills, and what you want to improve."
    return {"reply":answer,"mode":"built-in career guidance (no external LLM configured)","disclaimer":"General educational guidance; verify advice and real job details independently."}

@router.get("/dashboard")
def dashboard(user=Depends(current_user)):
    with db() as conn:
        history=conn.execute("SELECT id,profile,result_json,created_at FROM profile_history WHERE user_id=? ORDER BY id DESC LIMIT 10",(user["id"],)).fetchall()
        saved=conn.execute("SELECT j.id,j.title,j.company,j.location FROM saved_jobs s JOIN jobs j ON j.id=s.job_id WHERE s.user_id=? ORDER BY s.id DESC",(user["id"],)).fetchall()
        apps=conn.execute("SELECT * FROM applications WHERE user_id=? ORDER BY id DESC",(user["id"],)).fetchall()
    return {"user":user,"history":[{"id":r["id"],"profile":r["profile"],"matches":json.loads(r["result_json"]),"created_at":r["created_at"]} for r in history],"saved_jobs":[dict(r) for r in saved],"applications":[dict(r) for r in apps]}

@router.post("/history")
def save_history(body: dict, user=Depends(current_user)):
    profile=str(body.get("profile_text",""))[:50000]
    results=body.get("matches",[])
    with db() as conn:
        conn.execute("INSERT INTO profile_history(user_id,profile,result_json) VALUES(?,?,?)",(user["id"],profile,json.dumps(results)[:200000]))
    return {"saved":True}

@router.post("/saved-jobs")
def save_job(body: SavedBody, user=Depends(current_user)):
    with db() as conn:
        if not conn.execute("SELECT id FROM jobs WHERE id=?",(body.job_id,)).fetchone(): raise HTTPException(404,"Job not found.")
        conn.execute("INSERT OR IGNORE INTO saved_jobs(user_id,job_id) VALUES(?,?)",(user["id"],body.job_id))
    return {"saved":True}

@router.delete("/saved-jobs/{job_id}")
def unsave_job(job_id: int, user=Depends(current_user)):
    with db() as conn: conn.execute("DELETE FROM saved_jobs WHERE user_id=? AND job_id=?",(user["id"],job_id))
    return {"saved":False}

@router.post("/applications")
def add_application(body: ApplicationBody, user=Depends(current_user)):
    allowed={"Saved","Applied","Interview","Rejected","Offer"}
    if body.status not in allowed: raise HTTPException(400,"Choose a valid application status.")
    with db() as conn:
        cur=conn.execute("INSERT INTO applications(user_id,job_title,company,status,applied_date,notes) VALUES(?,?,?,?,?,?)",(user["id"],body.job_title.strip(),body.company.strip(),body.status,body.applied_date or time.strftime("%Y-%m-%d"),body.notes))
        row=conn.execute("SELECT * FROM applications WHERE id=?",(cur.lastrowid,)).fetchone()
    return dict(row)

@router.patch("/applications/{application_id}")
def update_application(application_id: int, body: ApplicationBody, user=Depends(current_user)):
    if body.status not in {"Saved","Applied","Interview","Rejected","Offer"}: raise HTTPException(400,"Choose a valid application status.")
    with db() as conn:
        cur=conn.execute("UPDATE applications SET job_title=?,company=?,status=?,applied_date=?,notes=? WHERE id=? AND user_id=?",(body.job_title,body.company,body.status,body.applied_date or time.strftime("%Y-%m-%d"),body.notes,application_id,user["id"]))
        if not cur.rowcount: raise HTTPException(404,"Application not found.")
        row=conn.execute("SELECT * FROM applications WHERE id=?",(application_id,)).fetchone()
    return dict(row)

@router.delete("/applications/{application_id}")
def delete_application(application_id: int, user=Depends(current_user)):
    with db() as conn: cur=conn.execute("DELETE FROM applications WHERE id=? AND user_id=?",(application_id,user["id"]))
    if not cur.rowcount: raise HTTPException(404,"Application not found.")
    return {"deleted":True}
