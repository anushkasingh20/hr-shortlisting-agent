"""
Security Utilities
"""

import re
import hashlib

INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?(instructions?|prompts?|system)",
    r"you are now",
    r"disregard",
    r"forget (everything|all|your instructions)",
    r"jailbreak",
]

_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def sanitise_input(text: str, max_length: int = 20000) -> str:
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    text = text[:max_length]
    text = _INJECTION_RE.sub("[REDACTED]", text)
    return text


def is_suspicious(text: str) -> bool:
    return bool(_INJECTION_RE.search(text))


def mask_pii(text: str) -> str:
    def _hash(m):
        h = hashlib.md5(m.group(0).encode()).hexdigest()[:6]
        return f"[MASKED:{h}]"
    text = re.sub(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", _hash, text)
    text = re.sub(r"(\+?\d[\d\s\-().]{8,}\d)", _hash, text)
    return text


def validate_score_output(score: dict) -> tuple:
    required = {"skills_match", "experience_relevance",
                "education_certs", "project_portfolio",
                "communication", "weighted_total", "recommendation"}
    missing = required - set(score.keys())
    if missing:
        return False, f"Missing keys: {missing}"
    total = score.get("weighted_total", -1)
    if not (0 <= total <= 10):
        return False, f"Total out of range: {total}"
    rec = score.get("recommendation", "")
    if rec not in {"HIRE", "MAYBE", "NO-HIRE"}:
        return False, f"Invalid recommendation: {rec}"
    return True, "OK"