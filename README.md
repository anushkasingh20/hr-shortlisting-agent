# HR Resume Shortlisting Agent
AI Enablement Internship — Task 1

## What it does
An AI agent that reads a Job Description and resumes, then produces a ranked shortlist with transparent scoring across 5 dimensions. Built to help HR teams screen candidates faster, consistently, and without bias.

## Features
- JD Parser — extracts skills, experience, domain from any Job Description
- Resume Ingestion — supports PDF, DOCX, TXT formats
- Scoring Rubric — 5 dimensions with weighted scoring (total 100%)
- Skill Gap Analysis — shows exactly what skills each candidate is missing
- Interview Questions — auto-generates questions based on candidate gaps
- HR Override — HR can manually adjust any score with a reason
- Reports — downloads HTML and JSON shortlist report

## Scoring Rubric
| Dimension | Weight |
|---|---|
| Skills Match | 30% |
| Experience Relevance | 25% |
| Project / Portfolio | 20% |
| Education & Certifications | 15% |
| Communication Quality | 10% |

## How to Run
Install dependencies and run the app:

    pip install streamlit langchain langchain-core pydantic python-dotenv pdfplumber python-docx
    python -m streamlit run app.py

Open browser at http://localhost:8501

## Tech Stack
- UI: Streamlit
- Framework: LangChain
- Resume Parsing: pdfplumber, python-docx
- Scoring: Custom heuristic engine (no API key required)
- Output: HTML and JSON reports

## Security
- Prompt injection filtering
- PII masking in logs
- Output schema validation
- API keys via .env file, never hardcoded

 ## Project Structure

    hr_agent/
    ├── app.py                  — Main Streamlit UI
    ├── agents/
    │   ├── jd_parser.py        — Parses Job Description
    │   ├── resume_parser.py    — Parses resumes
    │   ├── scoring_engine.py   — Scores candidates
    │   └── report_generator.py — Generates reports
    ├── utils/
    │   └── security.py         — Input sanitisation, PII masking
    ├── sample_data/            — Sample JD + 5 resumes
    └── outputs/                — Generated reports
