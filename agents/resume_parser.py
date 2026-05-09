"""
Resume Parser Agent
"""

import re
import json
from pathlib import Path


class ResumeParser:
    def __init__(self, llm=None):
        self.llm = llm

    def parse_file(self, file_path: str) -> dict:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = self._extract_pdf(file_path)
        elif suffix in (".docx", ".doc"):
            text = self._extract_docx(file_path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        profile = self._heuristic_parse(text)
        profile["raw_text"] = text
        profile["source_file"] = path.name
        return profile

    def parse_text(self, text: str, source_name: str = "manual_input") -> dict:
        profile = self._heuristic_parse(text)
        profile["raw_text"] = text
        profile["source_file"] = source_name
        return profile

    def _extract_pdf(self, path: str) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except:
            return ""

    def _extract_docx(self, path: str) -> str:
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except:
            return ""

    def _heuristic_parse(self, text: str) -> dict:
        lines = text.splitlines()
        text_lower = text.lower()

        name = next((l.strip() for l in lines if l.strip()), "Unknown")
        if len(name) > 50:
            name = "Unknown"

        email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
        email = email_match.group(0) if email_match else ""

        phone_match = re.search(r"(\+?\d[\d\s\-().]{8,}\d)", text)
        phone = phone_match.group(0).strip() if phone_match else ""

        skill_keywords = [
            "python", "java", "javascript", "typescript", "react", "angular",
            "node.js", "sql", "postgresql", "mysql", "mongodb", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "machine learning", "deep learning", "nlp", "llm", "langchain",
            "fastapi", "django", "flask", "spring", "git", "ci/cd",
            "spark", "kafka", "airflow", "dbt", "pandas", "numpy", "scikit-learn",
        ]
        skills = [s for s in skill_keywords if s in text_lower]

        exp_matches = re.findall(r"(\d{4})\s*[-–]\s*(\d{4}|present|current)", text_lower)
        total_exp = 0.0
        for start, end in exp_matches:
            end_year = 2024 if end in ("present", "current") else int(end)
            total_exp += max(0, end_year - int(start))

        cert_keywords = ["aws certified", "google certified", "azure certified",
                         "pmp", "cfa", "cpa", "scrum master", "cissp"]
        certs = [c for c in cert_keywords if c in text_lower]

        portfolio_match = re.search(r"(https?://(?:github|linkedin|portfolio)[^\s]+)", text_lower)
        portfolio = portfolio_match.group(0) if portfolio_match else ""

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "experience_years": round(total_exp, 1),
            "work_history": [],
            "education": [],
            "certifications": certs,
            "projects": [],
            "portfolio_url": portfolio,
        }