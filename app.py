"""
HR Resume Shortlisting Agent - Main App
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from pathlib import Path

from agents.jd_parser import JDParser
from agents.resume_parser import ResumeParser
from agents.scoring_engine import ScoringEngine, RUBRIC
from agents.report_generator import generate_html_report, generate_json_report
from utils.security import sanitise_input, is_suspicious, validate_score_output

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HR Shortlisting Agent",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] {
      background: #edf6ff;
      color: #000000;
  }
            
  h1, h2, h3, h4, h5, h6, p, span, label, div {
      color: black !important;
  }

  hr {
      border-color: black !important;
  }

  .stTabs [data-baseweb="tab"] {
      color: #2563eb !important;
  }

  .stMarkdown {
      color: black !important;
  }

  section[data-testid="stSidebar"] {
    background-color: #1e293b !important;
}

[data-testid="stSidebar"] * {
    color: white !important;
}
            
section[data-testid="stSidebar"] hr {
    border-color: white !important;
            
}
            
textarea {
    background-color: white !important;
}

[data-testid="stFileUploaderDropzone"] {
    background-color: white !important;
    border: none !important;
}
            
  .metric-box {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 1rem;
      text-align: center;
  }

  .stButton>button {
      border-radius: 8px;
      font-weight: 600;
      background: #3b82f6;
      color: white;
      border: none;
  }
  .stButton>button:hover {
      background: #2563eb;
  }
  #MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

for key, default in {
    "jd_parsed": None,
    "ranked": [],
    "overrides": {},
    "report_html_path": None,
    "report_json_path": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("##  HR Agent")
    st.markdown("---")
    st.markdown("### Rubric Weights")
    for dim, info in RUBRIC.items():
        st.markdown(f"**{info['label']}**: {int(info['weight']*100)}%")
    st.markdown("---")
    st.markdown("### 🛡️ Security Active")
    st.markdown(" Prompt injection filter")
    st.markdown(" PII masking in logs")
    st.markdown(" Output validation")
    st.markdown("---")
    st.markdown("### ℹ️ Mode")
    st.markdown("Running in **Heuristic Mode** — no API key needed.")

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("#  HR Resume Shortlisting Agent")
st.markdown("##### Upload a Job Description + resumes → get a ranked shortlist with transparent scoring")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["  Input & Run", "  Results", "  Report"])

# ════════════════════════════════════════
# TAB 1: INPUT
# ════════════════════════════════════════
with tab1:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### Job Description")

        if "jd_text" not in st.session_state:
            st.session_state.jd_text = ""

        if st.button("Load Sample JD", use_container_width=True):
            jd_file = Path("sample_data/job_description.txt")

            if jd_file.exists():
                st.session_state.jd_text = jd_file.read_text(encoding="utf-8")
                st.success("Sample JD loaded successfully.")
            else:
                st.error("Sample JD file not found.")

        jd_text = st.text_area(
            "Paste the Job Description here",
            height=300,
            placeholder="e.g. Senior Data Engineer – FinTech...",
            key="jd_text"
        )

    with col2:
        st.markdown("### 📄 Resumes")

        uploaded_files = st.file_uploader(
            "Upload resumes (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )

        use_samples = st.checkbox("Use 5 sample resumes instead", value=True)

        if use_samples:
            sample_files = list(Path("sample_data").glob("resume_*.txt"))
            st.success(f"{len(sample_files)} sample resumes ready")

            for f in sample_files:
                st.caption(f"📄 {f.name}")
    st.markdown("---")

    if st.button(" Run Shortlisting Agent", type="primary", use_container_width=True):
        if not jd_text or not jd_text.strip():
            st.error("Please provide a Job Description first.")
        else:
            with st.status("Running agent pipeline...", expanded=True) as status:

                st.write(" Step 1: Parsing Job Description...")
                jd_clean = sanitise_input(jd_text)
                if is_suspicious(jd_text):
                    st.warning("⚠️ Suspicious content detected in JD — sanitised.")
                jd_parser = JDParser(llm=None)
                jd_parsed = jd_parser.parse(jd_clean)
                st.session_state["jd_parsed"] = jd_parsed
                st.write(f" Role: **{jd_parsed['job_title']}** | Skills found: {len(jd_parsed['required_skills'])}")

                st.write(" Step 2: Parsing resumes...")
                resume_parser = ResumeParser(llm=None)
                candidates = []

                if use_samples:
                    for f in Path("sample_data").glob("resume_*.txt"):
                        text = sanitise_input(f.read_text())
                        profile = resume_parser.parse_text(text, source_name=f.name)
                        candidates.append(profile)
                else:
                    import tempfile
                    for uf in (uploaded_files or []):
                        with tempfile.NamedTemporaryFile(suffix=Path(uf.name).suffix, delete=False) as tmp:
                            tmp.write(uf.read())
                            tmp_path = tmp.name
                        profile = resume_parser.parse_file(tmp_path)
                        profile["source_file"] = uf.name
                        candidates.append(profile)

                st.write(f" Parsed {len(candidates)} resumes")

                st.write(" Step 3: Scoring candidates...")
                scorer = ScoringEngine(llm=None)
                for c in candidates:
                    scores = scorer.score(jd_parsed, c)
                    valid, msg = validate_score_output(scores)
                    if not valid:
                        st.warning(f"Score issue for {c.get('name','?')}: {msg}")
                    c["scores"] = scores

                st.write("Step 4: Ranking candidates...")
                ranked = sorted(candidates, key=lambda x: x["scores"]["weighted_total"], reverse=True)
                for i, c in enumerate(ranked, 1):
                    c["rank"] = i
                st.session_state["ranked"] = ranked

                os.makedirs("outputs", exist_ok=True)
                html_path = generate_html_report(jd_parsed, ranked, "outputs/shortlist_report.html")
                json_path = generate_json_report(jd_parsed, ranked, "outputs/shortlist_report.json")
                st.session_state["report_html_path"] = html_path
                st.session_state["report_json_path"] = json_path

                status.update(label="✅ Done! Go to Results tab.", state="complete")

           # st.balloons()

# ════════════════════════════════════════
# TAB 2: RESULTS
# ════════════════════════════════════════
with tab2:
    ranked = st.session_state["ranked"]
    jd_parsed = st.session_state["jd_parsed"]

    if not ranked:
        st.info("▶️ Run the agent first from the Input tab.")
    else:
        hire  = sum(1 for c in ranked if c["scores"]["recommendation"] == "HIRE")
        maybe = sum(1 for c in ranked if c["scores"]["recommendation"] == "MAYBE")
        no    = len(ranked) - hire - maybe

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Candidates", len(ranked))
        c2.metric(" HIRE", hire)
        c3.metric(" MAYBE", maybe)
        c4.metric(" NO-HIRE", no)

        st.markdown(f"### Ranked Shortlist — {jd_parsed.get('job_title','')}")
        st.markdown("---")

        for c in ranked:
            scores = c["scores"]
            rec = scores["recommendation"]
            emoji = {"HIRE": "✅", "MAYBE": "⚠️", "NO-HIRE": "❌"}.get(rec, "")
            color = {"HIRE": "green", "MAYBE": "orange", "NO-HIRE": "red"}.get(rec, "gray")

            with st.expander(
                f"#{c['rank']} · {c.get('name','Unknown')} — "
                f"{scores['weighted_total']:.1f}/10 · {emoji} :{color}[{rec}]",
                expanded=(c["rank"] <= 2),
            ):
                st.markdown(f" `{c.get('email','—')}` &nbsp;|&nbsp; "
                            f" `{c.get('experience_years',0)}y exp` &nbsp;|&nbsp; "
                            f" `{c.get('source_file','')}`")
                st.caption(scores.get("overall_summary", ""))

                st.markdown("#### Dimension Scores")
                for dim_key, info in RUBRIC.items():
                    dim_data = scores.get(dim_key, {})
                    s = dim_data.get("score", 0)
                    j = dim_data.get("justification", "")
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{info['label']}** ({int(info['weight']*100)}%)")
                        st.progress(int(s * 10))
                        st.caption(j)
                    with col_b:
                        st.markdown(f"### {s}/10")

                # ── Skill Gap Analysis (unique feature) ──────────────────────
                st.markdown("####  Skill Gap Analysis")
                required = set(jd_parsed.get("required_skills", []))
                candidate_skills = set(s.lower() for s in c.get("skills", []))
                missing = [s for s in required if s.lower() not in candidate_skills]
                if missing:
                    st.warning(f"Missing skills: **{', '.join(missing)}**")
                else:
                    st.success("Candidate has all required skills!")

                # ── Interview Questions (unique feature) ──────────────────────
                st.markdown("#### 💬 Suggested Interview Questions")
                questions = []
                if missing:
                    questions.append(f"You don't have {missing[0]} experience — how would you learn it?")
                exp = c.get("experience_years", 0)
                min_exp = jd_parsed.get("min_experience_years", 0)
                if exp < min_exp:
                    questions.append(f"This role needs {min_exp}y experience, you have {exp}y — walk us through your growth.")
                if c.get("projects"):
                    questions.append("Tell us about your most challenging project and what you learned.")
                questions.append("How do you ensure data quality in your pipelines?")
                for q in questions[:3]:
                    st.markdown(f"• {q}")

                # ── HR Override ───────────────────────────────────────────────
                st.markdown("####  HR Override")
                with st.form(key=f"override_{c['rank']}"):
                    dim_map = {
                        "Skills Match": "skills_match",
                        "Experience Relevance": "experience_relevance",
                        "Education & Certs": "education_certs",
                        "Project / Portfolio": "project_portfolio",
                        "Communication": "communication",
                    }
                    selected = st.selectbox("Dimension to override", list(dim_map.keys()))
                    new_score = st.slider("New score", 0.0, 10.0,
                                         value=float(scores.get(dim_map[selected], {}).get("score", 5)),
                                         step=0.5)
                    reason = st.text_input("Reason")
                    if st.form_submit_button("Apply Override"):
                        if reason:
                            scores[dim_map[selected]]["score"] = new_score
                            new_total = sum(scores[d]["score"] * RUBRIC[d]["weight"] for d in RUBRIC)
                            scores["weighted_total"] = round(new_total, 2)
                            st.success(f"Override applied! New total: {scores['weighted_total']}/10")
                            st.rerun()

# ════════════════════════════════════════
# TAB 3: REPORT
# ════════════════════════════════════════
with tab3:
    html_path = st.session_state["report_html_path"]
    json_path = st.session_state["report_json_path"]
    ranked    = st.session_state["ranked"]
    jd_parsed = st.session_state["jd_parsed"]

    if not ranked:
        st.info("▶️ Run the agent first from the Input tab.")
    else:
        st.markdown("### 📥 Download Reports")
        col1, col2 = st.columns(2)
        if html_path and Path(html_path).exists():
            with col1:
                with open(html_path, "rb") as f:
                    st.download_button(" Download HTML Report", data=f.read(),
                                       file_name="shortlist_report.html",
                                       mime="text/html", use_container_width=True)
        if json_path and Path(json_path).exists():
            with col2:
                with open(json_path, "rb") as f:
                    st.download_button(" Download JSON Data", data=f.read(),
                                       file_name="shortlist_report.json",
                                       mime="application/json", use_container_width=True)

        st.markdown("---")
        st.markdown("###  Report Preview")
        if html_path and Path(html_path).exists():
            with open(html_path, "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=700, scrolling=True)