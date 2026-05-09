"""
Report Generator
"""

import json
import os
from datetime import datetime
from pathlib import Path

RUBRIC_LABELS = {
    "skills_match":         ("Skills Match",          "30%"),
    "experience_relevance": ("Experience Relevance",  "25%"),
    "education_certs":      ("Education & Certs",     "15%"),
    "project_portfolio":    ("Project / Portfolio",   "20%"),
    "communication":        ("Communication Quality", "10%"),
}

RECOMMENDATION_COLORS = {
    "HIRE":    ("#16a34a", "#dcfce7"),
    "MAYBE":   ("#d97706", "#fef9c3"),
    "NO-HIRE": ("#dc2626", "#fee2e2"),
}


def generate_html_report(jd, ranked_candidates, output_path="outputs/shortlist_report.html", overrides=None):
    os.makedirs(Path(output_path).parent, exist_ok=True)
    overrides = overrides or {}
    html = _build_html(jd, ranked_candidates, overrides)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def generate_json_report(jd, ranked_candidates, output_path="outputs/shortlist_report.json"):
    os.makedirs(Path(output_path).parent, exist_ok=True)
    report = {
        "generated_at": datetime.now().isoformat(),
        "job_title": jd.get("job_title", "Unknown Role"),
        "total_candidates": len(ranked_candidates),
        "shortlist": [
            {
                "rank": c["rank"],
                "name": c.get("name", "Unknown"),
                "weighted_total": c["scores"]["weighted_total"],
                "recommendation": c["scores"]["recommendation"],
                "dimension_scores": {
                    k: {
                        "score": c["scores"][k]["score"],
                        "justification": c["scores"][k]["justification"],
                    }
                    for k in RUBRIC_LABELS
                },
                "overall_summary": c["scores"].get("overall_summary", ""),
            }
            for c in ranked_candidates
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return output_path


def _build_html(jd, candidates, overrides):
    rows = ""
    for c in candidates:
        scores = c["scores"]
        rec = scores.get("recommendation", "MAYBE")
        fg, bg = RECOMMENDATION_COLORS.get(rec, ("#374151", "#f3f4f6"))
        name = c.get("name", "Unknown")
        total = scores["weighted_total"]

        dim_rows = ""
        for dim_key, (dim_label, weight) in RUBRIC_LABELS.items():
            dim_data = scores.get(dim_key, {})
            score = dim_data.get("score", 0)
            just = dim_data.get("justification", "")
            bar_pct = int(score * 10)
            bar_color = "#16a34a" if score >= 7 else "#d97706" if score >= 5 else "#dc2626"
            dim_rows += f"""
            <tr>
              <td><b>{dim_label}</b> <span style="color:#888">{weight}</span></td>
              <td><div style="background:#f1f5f9;border-radius:4px;height:8px;width:120px">
                  <div style="width:{bar_pct}%;background:{bar_color};height:8px;border-radius:4px"></div>
                  </div></td>
              <td><b>{score}/10</b></td>
              <td style="color:#555">{just}</td>
            </tr>"""

        rows += f"""
        <div style="background:white;border:1px solid #e2e8f0;border-left:5px solid {fg};
                    border-radius:12px;padding:1.5rem;margin-bottom:1.5rem">
          <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
            <span style="font-size:2rem;font-weight:800;color:#888">#{c['rank']}</span>
            <div>
              <h3 style="margin:0">{name}</h3>
              <span style="color:#888;font-size:.85rem">{c.get('email','')} | {c.get('source_file','')}</span>
            </div>
            <div style="margin-left:auto;text-align:center;background:{bg};
                        color:{fg};padding:.75rem 1.25rem;border-radius:10px">
              <div style="font-size:2rem;font-weight:800;line-height:1">{total}</div>
              <div style="font-size:.75rem">/10</div>
              <div style="font-size:.75rem;font-weight:700">{rec}</div>
            </div>
          </div>
          <p style="color:#555;margin-bottom:1rem">{scores.get('overall_summary','')}</p>
          <table style="width:100%;border-collapse:collapse;font-size:.85rem">
            <tr style="color:#888;border-bottom:1px solid #e2e8f0">
              <th style="text-align:left;padding:.4rem">Dimension</th>
              <th>Score Bar</th><th>Score</th>
              <th style="text-align:left">Justification</th>
            </tr>
            {dim_rows}
          </table>
        </div>"""

    jd_skills = ", ".join(jd.get("required_skills", [])) or "—"
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>HR Shortlist Report</title>
<style>body{{font-family:system-ui,sans-serif;background:#f8fafc;padding:2rem;color:#1e293b}}</style>
</head><body>
<div style="background:#1e293b;color:#f8fafc;padding:2rem;border-radius:12px;margin-bottom:2rem">
  <h1 style="margin:0 0 .5rem">📋 HR Shortlist Report</h1>
  <p style="color:#94a3b8;margin:0">AI-generated ranking — human review required.</p>
  <div style="display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap">
    <span style="background:#334155;padding:.4rem 1rem;border-radius:8px">
      <b style="color:#93c5fd">Role:</b> {jd.get('job_title','Unknown')}</span>
    <span style="background:#334155;padding:.4rem 1rem;border-radius:8px">
      <b style="color:#93c5fd">Candidates:</b> {len(candidates)}</span>
    <span style="background:#334155;padding:.4rem 1rem;border-radius:8px">
      <b style="color:#93c5fd">Generated:</b> {datetime.now().strftime('%d %b %Y %H:%M')}</span>
    <span style="background:#334155;padding:.4rem 1rem;border-radius:8px">
      <b style="color:#93c5fd">Skills:</b> {jd_skills}</span>
  </div>
</div>
{rows}
<p style="text-align:center;color:#888;font-size:.8rem">HR Shortlisting Agent · {datetime.now().year}</p>
</body></html>"""