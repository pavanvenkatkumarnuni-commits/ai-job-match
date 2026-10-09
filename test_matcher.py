from matcher import extract_skills, match_jobs

def test_extracts_known_skills():
    result = extract_skills("I use Python, SQL and React.", ["Python", "SQL", "React", "Machine Learning"])
    assert {"python", "sql", "react"}.issubset(set(result))
    assert "machine learning" not in result

def test_javascript_is_not_java():
    result = extract_skills("I build apps using JavaScript.", ["Java", "JavaScript"])
    assert "javascript" in result
    assert "java" not in result

def test_match_jobs_returns_sorted_scores():
    jobs = [
        {"id": 1, "title": "Python Developer", "company": "Demo", "description": "Python apps with SQL and FastAPI.", "skills": ["Python", "SQL", "FastAPI"], "experience": "Entry level", "location": "Remote"},
        {"id": 2, "title": "Frontend Developer", "company": "Demo", "description": "React apps with JavaScript and CSS.", "skills": ["React", "JavaScript", "CSS"], "experience": "Entry level", "location": "Remote"},
    ]
    result = match_jobs("Python SQL FastAPI backend developer", jobs)
    assert len(result) == 2
    assert result[0]["match_score"] >= result[1]["match_score"]
    assert "matched_skills" in result[0]
