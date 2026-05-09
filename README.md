# 🎯 HR Resume Shortlisting Agent
> AI Enablement Internship — Task 1

## What it does
An AI agent that reads a Job Description + resumes and produces a ranked shortlist with transparent scoring across 5 dimensions.

## Features
- ✅ JD Parser — extracts skills, experience, domain from any JD
- ✅ Resume Ingestion — supports PDF, DOCX, TXT
- ✅ Scoring Rubric — 5 dimensions with weighted scoring
- ✅ Skill Gap Analysis — shows exactly what skills candidate is missing
- ✅ Interview Questions — auto-generates questions based on gaps
- ✅ HR Override — HR can manually adjust any score with a reason
- ✅ Reports — downloads HTML and JSON shortlist report

## How to run
```bash
pip install streamlit langchain langchain-core pydantic python-dotenv pdfplumber python-docx
python -m streamlit run app.py
```

## Tech Stack
- LLM: GPT-4o / Claude Sonnet (heuristic mode if no API key — no API key required to run)
- Framework: LangChain
- UI: Streamlit
- Resume Parsing: pdfplumber, python-docx

## Security
- Prompt injection filtering
- PII masking in logs
- Output schema validation
- API keys via .env file
