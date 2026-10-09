import os
import re
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_ALIASES = {"ml": "machine learning", "js": "javascript", "scikit learn": "scikit-learn", "rest apis": "rest api", "postgresql": "sql"}
KNOWN_SKILLS = sorted({
    "Python", "SQL", "Git", "FastAPI", "Testing", "Machine Learning",
    "scikit-learn", "pandas", "NumPy", "Statistics", "React", "JavaScript",
    "HTML", "CSS", "REST API", "Excel", "Data Visualization", "pytest",
    "API Testing", "Debugging", "Docker", "Java", "C++", "C#", "Django",
    "Flask", "AWS", "Communication", "Problem Solving", "Linux", "Power BI"
})

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def canonical_skill(skill: str) -> str:
    value = normalize(skill)
    return SKILL_ALIASES.get(value, value)

def extract_skills(text: str, known_skills=None):
    known_skills = known_skills or KNOWN_SKILLS
    normalized = normalize(text)
    found = set()
    for skill in known_skills:
        candidate = canonical_skill(skill)
        if candidate:
            pattern = r"(?<![a-z0-9+#])" + re.escape(candidate) + r"(?![a-z0-9+#])"
            if re.search(pattern, normalized):
                found.add(candidate)
    return sorted(found)

@lru_cache(maxsize=1)
def _sentence_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def _similarity_scores(profile_text, job_texts):
    if os.getenv("USE_SENTENCE_TRANSFORMERS", "false").lower() == "true":
        model = _sentence_model()
        vectors = model.encode([profile_text, *job_texts], normalize_embeddings=True)
        scores = np.asarray(vectors[1:] @ vectors[0], dtype=float)
        return np.clip(scores, 0.0, 1.0) * 100
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform([profile_text, *job_texts])
    scores = cosine_similarity(matrix[0:1], matrix[1:])[0]
    return np.clip(scores, 0.0, 1.0) * 100

def match_jobs(profile_text, jobs):
    if not jobs:
        return []
    all_skills = sorted({s for job in jobs for s in job["skills"]} | set(KNOWN_SKILLS))
    candidate_skills = set(extract_skills(profile_text, all_skills))
    job_texts = [
        f'{job["title"]}. {job["description"]}. Required skills: {", ".join(job["skills"])}'
        for job in jobs
    ]
    text_scores = _similarity_scores(profile_text, job_texts)
    results = []
    for index, job in enumerate(jobs):
        required = {canonical_skill(skill) for skill in job["skills"]}
        matched = sorted(required & candidate_skills)
        missing = sorted(required - candidate_skills)
        skill_score = 100 * len(matched) / len(required) if required else 0.0
        text_score = float(text_scores[index])
        final_score = 0.60 * skill_score + 0.40 * text_score
        results.append({
            "id": job["id"], "title": job["title"], "company": job["company"],
            "description": job["description"], "experience": job["experience"],
            "location": job.get("location", "Not specified"),
            "match_score": round(float(final_score), 1),
            "skill_score": round(float(skill_score), 1),
            "semantic_score": round(text_score, 1),
            "matched_skills": matched, "missing_skills": missing,
        })
    return sorted(results, key=lambda item: item["match_score"], reverse=True)
