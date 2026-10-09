import { useState } from "react";
import { BriefcaseBusiness, BrainCircuit, FileText, Sparkles, Upload, CheckCircle2, AlertCircle, MapPin } from "lucide-react";
import "./App.css";

function Tags({ items, variant = "matched" }) {
  if (!items?.length) return <span className="muted small">None identified</span>;
  return <div className="tags">{items.map(item => <span className={`tag ${variant}`} key={item}>{item}</span>)}</div>;
}

function JobCard({ job }) {
  return <article className="job-card">
    <div className="job-top">
      <div className="job-icon"><BriefcaseBusiness size={21}/></div>
      <div className="job-title"><h3>{job.title}</h3><p>{job.company}</p><span className="location"><MapPin size={13}/> {job.location} · {job.experience}</span></div>
      <div className="score"><strong>{job.match_score}%</strong><span>match</span></div>
    </div>
    <div className="track"><div className="track-fill" style={{width: `${job.match_score}%`}}/></div>
    <p className="description">{job.description}</p>
    <div className="score-breakdown"><span>Skill overlap <b>{job.skill_score}%</b></span><span>Text similarity <b>{job.semantic_score}%</b></span></div>
    <section className="skill-section"><h4><CheckCircle2 size={15}/> Matching skills</h4><Tags items={job.matched_skills}/></section>
    <section className="skill-section"><h4><Sparkles size={15}/> Skills to develop</h4><Tags items={job.missing_skills} variant="missing"/></section>
  </article>;
}

export default function App() {
  const [profile, setProfile] = useState("");
  const [resume, setResume] = useState(null);
  const [matches, setMatches] = useState([]);
  const [candidateSkills, setCandidateSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  async function findMatches(event) {
    event.preventDefault(); setLoading(true); setError(""); setMatches([]); setHasSearched(false);
    try {
      const form = new FormData();
      form.append("profile_text", profile);
      if (resume) form.append("resume", resume);
      const response = await fetch("/api/match", { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Matching failed.");
      setMatches(payload.matches); setCandidateSkills(payload.candidate_skills); setHasSearched(true);
    } catch (err) {
      setError(err.message || "Could not connect to the server. Try again.");
    } finally { setLoading(false); }
  }

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="#"><span className="brand-mark">JM</span><span>Job<span className="brand-accent">Match</span><small>AI CAREER DISCOVERY</small></span></a>
      <span className="top-chip"><span className="live-dot"/> HYBRID AI MATCHING</span>
    </header>
    <main>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow"><Sparkles size={14}/> CAREER DISCOVERY, REIMAGINED</span>
          <h1>Your skills.<br/><span>Your next opportunity.</span></h1>
          <p>Discover roles that fit your experience. Our hybrid matcher compares your skills and profile text with job requirements, then explains where you match and what to learn next.</p>
          <div className="hero-points"><span><CheckCircle2 size={16}/> Explainable results</span><span><CheckCircle2 size={16}/> Resume PDF support</span></div>
        </div>
        <div className="hero-visual"><div className="visual-orbit orbit-one"/><div className="visual-orbit orbit-two"/><div className="visual-core"><BrainCircuit size={43}/></div>
          <div className="float-card float-top"><span className="mini-icon"><FileText size={16}/></span><span><b>Resume analyzed</b><small>Skills and experience</small></span><CheckCircle2 className="float-check" size={17}/></div>
          <div className="float-card float-bottom"><span className="mini-icon purple"><Sparkles size={16}/></span><span><b>Smart recommendations</b><small>Ranked by profile fit</small></span></div>
        </div>
      </section>
      <section className="workspace">
        <form className="profile-panel" onSubmit={findMatches}>
          <div className="panel-heading"><span className="step">01</span><div><h2>Build your profile</h2><p>Share your skills, projects, or resume.</p></div></div>
          <label htmlFor="profile">PROFILE DETAILS <span>Optional if uploading a resume</span></label>
          <textarea id="profile" value={profile} onChange={e => setProfile(e.target.value)} placeholder="I'm a computer science student skilled in Python, SQL, React and machine learning. I built a student performance prediction project..." rows={7}/>
          <div className="upload-label"><label htmlFor="resume">UPLOAD RESUME <span>PDF · 5 MB max</span></label></div>
          <label className="upload-zone" htmlFor="resume"><span className="upload-icon"><Upload size={21}/></span><span><b>{resume ? resume.name : "Choose your resume PDF"}</b><small>{resume ? "Selected file" : "Click to browse your files"}</small></span><input id="resume" type="file" accept=".pdf,application/pdf" onChange={e => setResume(e.target.files?.[0] || null)}/></label>
          <button className="submit-button" type="submit" disabled={loading}><span>{loading ? "Analyzing profile..." : "Find my matching jobs"}</span><Sparkles size={17}/></button>
          {error && <div className="error-message"><AlertCircle size={17}/>{error}</div>}
          <p className="privacy-note"><FileText size={14}/> Resume content is processed for this request; this demo does not save uploaded resumes.</p>
        </form>
        <aside className="tips-panel">
          <div className="tips-head"><div className="tips-icon"><Sparkles size={19}/></div><span>PRO TIP</span></div>
          <h3>Make your profile count.</h3><p>The more relevant detail you include, the more useful your recommendations can be.</p>
          <ul><li><CheckCircle2 size={16}/> Technical skills and tools</li><li><CheckCircle2 size={16}/> Projects and coursework</li><li><CheckCircle2 size={16}/> Internships or experience</li><li><CheckCircle2 size={16}/> Certifications and achievements</li></ul>
          <div className="how-box"><BrainCircuit size={20}/><div><b>How matching works</b><p>60% required-skill overlap + 40% text similarity. Scores are estimates, not hiring probabilities.</p></div></div>
        </aside>
      </section>
      {hasSearched && <section className="results-section">
        <div className="results-title"><div><span className="eyebrow">02 / YOUR RESULTS</span><h2>Recommended for you</h2><p>Roles are ranked by estimated profile similarity.</p></div><div className="results-count"><b>{matches.length}</b><span>jobs analyzed</span></div></div>
        <div className="candidate-skills"><div><b>Skills detected in your profile</b><p>Known skills found among the job requirements.</p></div><Tags items={candidateSkills}/></div>
        <div className="job-grid">{matches.map(job => <JobCard key={job.id} job={job}/>)}</div>
      </section>}
      {!hasSearched && <section className="empty-state"><div className="empty-icon"><BriefcaseBusiness size={24}/></div><div><b>Your next role starts here</b><p>Submit your profile to see ranked job recommendations and skill gaps.</p></div><span className="empty-step">READY WHEN YOU ARE</span></section>}
    </main>
    <footer><a className="footer-brand" href="#">JobMatch AI</a><span>College project · Demo job listings</span><span className="footer-disclaimer">AI scores support exploration; review every role yourself.</span></footer>
  </div>;
}
