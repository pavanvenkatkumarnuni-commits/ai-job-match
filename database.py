import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "jobs.db")))

SAMPLE_JOBS = [
    {"title": "Python Developer", "company": "TechNova (Demo)", "description": "Build Python applications and REST APIs. Work with SQL databases, Git, testing and FastAPI.", "skills": ["Python", "SQL", "Git", "FastAPI", "Testing"], "experience": "Entry level", "location": "Remote (Demo)"},
    {"title": "Machine Learning Engineer", "company": "DataSpark (Demo)", "description": "Develop machine learning models using Python, scikit-learn, pandas, NumPy and model evaluation.", "skills": ["Python", "Machine Learning", "scikit-learn", "pandas", "NumPy", "Statistics"], "experience": "Entry level", "location": "Hyderabad (Demo)"},
    {"title": "Frontend Developer", "company": "PixelWorks (Demo)", "description": "Create responsive web applications using React, JavaScript, HTML, CSS and REST APIs.", "skills": ["React", "JavaScript", "HTML", "CSS", "REST API"], "experience": "Entry level", "location": "Remote (Demo)"},
    {"title": "Data Analyst", "company": "InsightHub (Demo)", "description": "Analyze datasets using Python, SQL, Excel, statistics and data visualization tools.", "skills": ["Python", "SQL", "Excel", "Statistics", "Data Visualization", "pandas"], "experience": "Entry level", "location": "Bengaluru (Demo)"},
    {"title": "Full Stack Developer", "company": "WebBridge (Demo)", "description": "Build web applications with React, Python, FastAPI, SQL databases, Git and REST APIs.", "skills": ["React", "Python", "FastAPI", "SQL", "Git", "REST API"], "experience": "Entry level", "location": "Hybrid (Demo)"},
    {"title": "Junior QA Automation Engineer", "company": "QualityLoop (Demo)", "description": "Write automated tests for web applications. Use Python, pytest, API testing, Git and debugging.", "skills": ["Python", "pytest", "API Testing", "Git", "Debugging"], "experience": "Entry level", "location": "Chennai (Demo)"},
]

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, company TEXT NOT NULL,
                description TEXT NOT NULL, skills TEXT NOT NULL,
                experience TEXT NOT NULL, location TEXT NOT NULL
            )
        """)
        if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            for job in SAMPLE_JOBS:
                conn.execute(
                    "INSERT INTO jobs (title, company, description, skills, experience, location) VALUES (?, ?, ?, ?, ?, ?)",
                    (job["title"], job["company"], job["description"], json.dumps(job["skills"]), job["experience"], job["location"])
                )

def get_jobs():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
    jobs = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item["skills"])
        jobs.append(item)
    return jobs
