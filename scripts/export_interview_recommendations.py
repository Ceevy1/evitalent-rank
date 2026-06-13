from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.interview.interview_recommendation_service import InterviewRecommendationService


DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "interview_recommendations"
SAFE_RANKING_PATH = ROOT / "data" / "outputs" / "official_samples_v1" / "rankings" / "all_domains_safe_summary.json"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {"domains": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _analysis_from_item(item: dict, domain: str) -> dict:
    return {
        "candidate_id": item.get("document_id"),
        "target_domain": domain,
        "job_title": f"{domain} 目标岗位",
        "rank_score": item.get("rank_score", 0),
        "bcs": item.get("bcs", 0),
        "eci": item.get("eci", 0),
        "penalty": item.get("penalty", 0),
        "axis_scores": {},
        "top_strengths": [{"label": label, "score": 75} for label in item.get("top_strength_labels", [])],
        "risk_flags": item.get("risk_flag_types", []),
        "normalized_achievement_events": [],
        "grounded_evidence_items": [],
        "career_records": [],
    }


def _html_fragment(payload: dict) -> str:
    questions = "".join(f"<li>{escape(item['question'])}</li>" for item in payload.get("recommended_questions", []))
    return (
        f"<section><h3>{escape(payload['candidate_id'])}</h3>"
        f"<p>{escape(payload['fit_summary'])}</p>"
        f"<ul>{questions}</ul>"
        "<p>仅用于面试辅助，不构成录用或淘汰决定。</p></section>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export safe interview focus recommendations.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    service = InterviewRecommendationService()
    count = 0
    payload = _read_json(SAFE_RANKING_PATH)
    for domain, domain_payload in payload.get("domains", {}).items():
        for item in domain_payload.get("ranking", []):
            recommendation = service.recommend(_analysis_from_item(item, domain))
            data = recommendation.model_dump(mode="json")
            candidate_id = data["candidate_id"]
            (args.output_dir / f"{candidate_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            (args.output_dir / f"{candidate_id}.html").write_text(_html_fragment(data), encoding="utf-8")
            count += 1
    print(f"output_dir={args.output_dir}")
    print(f"exported_recommendations={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
