
"""
JD Parser Agent
Extracts structured requirements from a Job Description using an LLM.
Falls back to keyword heuristics if LLM is unavailable.
"""

import os
import json
import re
from typing import Optional


class JobRequirements:
    def __init__(self, data: dict):
        self.job_title = data.get("job_title", "Unknown Role")
        self.required_skills = data.get("required_skills", [])
        self.preferred_skills = data.get("preferred_skills", [])
        self.min_experience_years = data.get("min_experience_years", 0)
        self.education = data.get("education", "Not specified")
        self.certifications = data.get("certifications", [])
        self.domain = data.get("domain", "Technology")
        self.seniority = data.get("seniority", "Mid")
        self.key_responsibilities = data.get("key_responsibilities", [])

    def to_dict(self):
        return self.__dict__


class JDParser:
    def __init__(self, llm=None):
        self.llm = llm

    def parse(self, jd_text: str) -> dict:
        if self.llm:
            return self._llm_parse(jd_text)
        return self._heuristic_parse(jd_text)

    def _llm_parse(self, jd_text: str) -> dict:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert HR analyst. Extract structured information from the Job Description.
Return ONLY valid JSON with these keys:
job_title, required_skills (list), preferred_skills (list), min_experience_years (int),
education (str), certifications (list), domain (str), seniority (str), key_responsibilities (list).
No markdown, no extra text."""),
            ("human", "Job Description:\n\n{jd_text}"),
        ])
        chain = prompt | self.llm
        result = chain.invoke({"jd_text": jd_text[:8000]})
        text = result.content if hasattr(result, 'content') else str(result)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    def _heuristic_parse(self, jd_text: str) -> dict:
        text_lower = jd_text.lower()

        exp_match = re.search(r"(\d+)\+?\s*years?", text_lower)
        exp_years = int(exp_match.group(1)) if exp_match else 0

        education = "Not specified"
        for edu in ["phd", "master", "bachelor", "b.tech", "b.e", "mba"]:
            if edu in text_lower:
                education = edu.upper()
                break

        seniority = "Mid"
        for level in ["junior", "senior", "lead", "manager", "director", "intern"]:
            if level in text_lower:
                seniority = level.capitalize()
                break

        skill_keywords = [
            "python", "java", "javascript", "typescript", "react", "node", "sql",
            "aws", "azure", "gcp", "docker", "kubernetes", "ml", "llm", "langchain",
            "fastapi", "django", "flask", "spring", "postgresql", "mongodb", "redis",
            "spark", "kafka", "airflow", "dbt", "terraform", "ci/cd", "git",
        ]
        found_skills = [s for s in skill_keywords if s in text_lower]

        return {
            "job_title":            _extract_title(jd_text),
            "required_skills":      found_skills[:8],
            "preferred_skills":     found_skills[8:],
            "min_experience_years": exp_years,
            "education":            education,
            "certifications":       [],
            "domain":               "Technology",
            "seniority":            seniority,
            "key_responsibilities": [],
        }


def _extract_title(text: str) -> str:
    for line in text.strip().splitlines():
        line = line.strip()
        if line and len(line) < 80:
            return line
    return "Unknown Role"
