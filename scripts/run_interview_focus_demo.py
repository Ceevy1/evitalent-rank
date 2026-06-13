from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import ECOMMERCE_MULTI_ACHIEVEMENT_TEXT, HR_MULTI_ACHIEVEMENT_TEXT, PRODUCTION_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline
from evitalent.interview.interview_recommendation_service import InterviewRecommendationService
from evitalent.scoring.ranker import rank_candidates


SAMPLES = {
    "hr": HR_MULTI_ACHIEVEMENT_TEXT,
    "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
    "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
}


def _analysis(domain: str, text: str) -> dict:
    result = HybridExtractionPipeline().extract(text, f"interview_doc_{domain}", f"interview_candidate_{domain}")
    ranking = rank_candidates([result.candidate_extraction], domain).candidates[0]
    return {
        "candidate_id": result.candidate_extraction.candidate_id,
        "target_domain": domain,
        "job_title": f"{domain} 目标岗位",
        "rank_score": ranking.rank_score,
        "bcs": ranking.bcs,
        "eci": ranking.eci,
        "penalty": ranking.penalty,
        "axis_scores": ranking.axis_scores,
        "top_strengths": ranking.top_strengths,
        "risk_flags": ranking.risk_flags,
        "normalized_achievement_events": result.candidate_extraction.achievement_events,
        "grounded_evidence_items": result.candidate_extraction.evidence_items,
        "career_records": result.candidate_extraction.career_records,
    }


def main() -> int:
    service = InterviewRecommendationService()
    for domain, text in SAMPLES.items():
        recommendation = service.recommend(_analysis(domain, text))
        print(f"candidate_id={recommendation.candidate_id}")
        print(f"high_fit_conditions={len(recommendation.high_fit_conditions)}")
        print(f"interview_focus_areas={len(recommendation.interview_focus_areas)}")
        print(f"recommended_questions={len(recommendation.recommended_questions)}")
        print(f"risk_verification_items={len(recommendation.risk_verification_items)}")
        print(f"safety_passed={recommendation.safety_passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
