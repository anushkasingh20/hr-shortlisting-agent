"""
Scoring Engine
"""

RUBRIC = {
    "skills_match":         {"weight": 0.30, "label": "Skills Match"},
    "experience_relevance": {"weight": 0.25, "label": "Experience Relevance"},
    "education_certs":      {"weight": 0.15, "label": "Education & Certifications"},
    "project_portfolio":    {"weight": 0.20, "label": "Project / Portfolio"},
    "communication":        {"weight": 0.10, "label": "Communication Quality"},
}


class ScoringEngine:
    def __init__(self, llm=None):
        self.llm = llm

    def score(self, jd: dict, candidate: dict) -> dict:
        if self.llm:
            return self._llm_score(jd, candidate)
        return self._heuristic_score(jd, candidate)

    def score_batch(self, jd: dict, candidates: list) -> list:
        scored = []
        for c in candidates:
            score_data = self.score(jd, c)
            scored.append({**c, "scores": score_data})
        scored.sort(key=lambda x: x["scores"]["weighted_total"], reverse=True)
        for i, c in enumerate(scored, 1):
            c["rank"] = i
        return scored

    def _llm_score(self, jd: dict, candidate: dict) -> dict:
        import json
        from langchain_core.prompts import ChatPromptTemplate

        safe_candidate = {k: v for k, v in candidate.items() if k != "raw_text"}
        prompt = ChatPromptTemplate.from_messages([
            ("human", """You are a senior HR evaluator. Score this candidate for the role.

Job Requirements:
{jd_json}

Candidate Profile:
{candidate_json}

Score across 5 dimensions (0-10 each):
1. Skills Match (30%): how many required skills does candidate have?
2. Experience Relevance (25%): years and domain match?
3. Education & Certifications (15%): meets requirements?
4. Project / Portfolio (20%): relevant projects?
5. Communication Quality (10%): resume clarity and structure?

Return ONLY valid JSON, no markdown:
{{
  "skills_match": {{"score": 7.5, "justification": "one line reason"}},
  "experience_relevance": {{"score": 8.0, "justification": "one line reason"}},
  "education_certs": {{"score": 6.0, "justification": "one line reason"}},
  "project_portfolio": {{"score": 7.0, "justification": "one line reason"}},
  "communication": {{"score": 8.0, "justification": "one line reason"}},
  "weighted_total": 7.4,
  "recommendation": "HIRE",
  "overall_summary": "2-3 sentence summary"
}}"""),
        ])
        chain = prompt | self.llm
        result = chain.invoke({
            "jd_json": json.dumps(jd, indent=2)[:3000],
            "candidate_json": json.dumps(safe_candidate, indent=2)[:3000],
        })
        text = result.content if hasattr(result, 'content') else str(result)
        text = text.replace("```json", "").replace("```", "").strip()
        raw = json.loads(text)
        return self._compute_total(raw)

    def _heuristic_score(self, jd: dict, candidate: dict) -> dict:
        required_skills  = {s.lower() for s in jd.get("required_skills", [])}
        candidate_skills = {s.lower() for s in candidate.get("skills", [])}
        min_exp  = jd.get("min_experience_years", 0)
        cand_exp = candidate.get("experience_years", 0)

        if required_skills:
            overlap = len(required_skills & candidate_skills) / len(required_skills)
        else:
            overlap = 0.5
        skills_score = round(min(10, overlap * 10 * 1.1), 1)
        skills_just  = f"{int(overlap*100)}% of required skills found."

        exp_ratio = (cand_exp / max(min_exp, 1)) if min_exp else 1.0
        exp_score = round(min(10, exp_ratio * 7), 1)
        exp_just  = f"{cand_exp}y experience vs {min_exp}y required."

        edu_score = 5.0
        certs = candidate.get("certifications", [])
        if certs:
            edu_score = min(10, 5 + len(certs) * 1.5)
        edu_just = f"{'Has ' + str(len(certs)) + ' cert(s).' if certs else 'No certs detected.'}"

        projects  = candidate.get("projects", [])
        portfolio = candidate.get("portfolio_url", "")
        proj_score = 3.0
        if projects:
            proj_score = min(10, 5 + len(projects) * 1.5)
        if portfolio:
            proj_score = min(10, proj_score + 1.5)
        proj_just = f"{len(projects)} project(s); portfolio {'present' if portfolio else 'absent'}."

        raw_text   = candidate.get("raw_text", "")
        word_count = len(raw_text.split())
        comm_score = 5.0
        if word_count > 400:
            comm_score = 7.0
        if word_count > 700:
            comm_score = 8.5
        comm_just = f"Resume ~{word_count} words."

        raw = {
            "skills_match":         {"score": skills_score, "justification": skills_just},
            "experience_relevance": {"score": exp_score,    "justification": exp_just},
            "education_certs":      {"score": edu_score,    "justification": edu_just},
            "project_portfolio":    {"score": proj_score,   "justification": proj_just},
            "communication":        {"score": comm_score,   "justification": comm_just},
        }
        return self._compute_total(raw)

    @staticmethod
    def _compute_total(raw: dict) -> dict:
        total = sum(
            raw[dim]["score"] * info["weight"]
            for dim, info in RUBRIC.items()
            if dim in raw
        )
        total = round(total, 2)
        raw["weighted_total"] = total
        if "recommendation" not in raw:
            if total >= 7:
                raw["recommendation"] = "HIRE"
            elif total >= 5:
                raw["recommendation"] = "MAYBE"
            else:
                raw["recommendation"] = "NO-HIRE"
        if "overall_summary" not in raw:
            raw["overall_summary"] = f"Weighted score: {total}/10. Recommendation: {raw['recommendation']}."
        return raw