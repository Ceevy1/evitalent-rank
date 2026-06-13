from __future__ import annotations

from evitalent.models.extraction import AchievementEvent, CandidateExtraction, EvidenceGrade
from evitalent.utils import clamp


SCORABLE_GRADES = {EvidenceGrade.A, EvidenceGrade.B}

BUSINESS_RELEVANCE = {
    "revenue_growth": 20,
    "gmv_growth": 20,
    "roi_improvement": 18,
    "conversion_improvement": 18,
    "cost_reduction": 18,
    "efficiency_improvement": 18,
    "loss_reduction": 18,
    "quality_improvement": 16,
    "recruitment_delivery": 18,
    "recruitment_completion_rate": 17,
    "retention_improvement": 17,
    "organization_transformation": 14,
    "product_launch": 19,
    "automation_upgrade": 18,
    "promotion_award": 12,
    "patent_publication": 15,
    "technology_transfer": 20,
    "collection_performance": 16,
    "channel_expansion": 17,
    "other": 10,
}


def scorable_achievements(candidate: CandidateExtraction) -> list[AchievementEvent]:
    return [event for event in candidate.achievement_events if event.evidence_grade in SCORABLE_GRADES]


def quantified_achievement_count(candidate: CandidateExtraction) -> tuple[int, list[str]]:
    events = [event for event in scorable_achievements(candidate) if event.metric_value is not None]
    return len(events), [event.evidence_id for event in events]


def _magnitude_score(event: AchievementEvent) -> float:
    value = event.metric_value
    if value is None:
        return 12.0
    unit = (event.unit or "").lower()
    event_type = event.event_type.value
    if event_type in {"revenue_growth", "gmv_growth", "technology_transfer"}:
        if unit in {"万元", "万", "w"}:
            return clamp(10 + value / 250.0, 0, 30)
        return clamp(10 + value / 1000000.0, 0, 30)
    if event_type in {"roi_improvement", "conversion_improvement", "efficiency_improvement", "loss_reduction", "quality_improvement", "retention_improvement", "recruitment_completion_rate", "collection_performance"}:
        return clamp(10 + value * 1.2, 0, 30)
    if event_type == "recruitment_delivery":
        return clamp(8 + value * 0.8, 0, 30)
    if event_type in {"product_launch", "patent_publication", "automation_upgrade", "channel_expansion"}:
        return clamp(10 + value * 4.0, 0, 30)
    return clamp(10 + value, 0, 30)


def score_achievement_event(event: AchievementEvent) -> dict[str, float]:
    if event.evidence_grade not in SCORABLE_GRADES:
        return {
            "metric_specificity": 0.0,
            "result_magnitude": 0.0,
            "role_contribution": 0.0,
            "business_relevance": 0.0,
            "total": 0.0,
        }
    metric_specificity = 25.0 if event.metric_value is not None and event.period_months is not None else 18.0 if event.metric_value is not None else 10.0
    result_magnitude = _magnitude_score(event)
    contribution_text = event.candidate_contribution or ""
    role_contribution = 25.0 if any(term in contribution_text for term in ("主导", "负责", "推动", "管理")) else 17.0
    business_relevance = float(BUSINESS_RELEVANCE.get(event.event_type.value, 10))
    grade_factor = 1.0 if event.evidence_grade == EvidenceGrade.A else 0.85
    total = (metric_specificity + result_magnitude + role_contribution + business_relevance) * grade_factor
    return {
        "metric_specificity": round(metric_specificity, 2),
        "result_magnitude": round(result_magnitude, 2),
        "role_contribution": round(role_contribution, 2),
        "business_relevance": round(business_relevance, 2),
        "total": round(clamp(total), 2),
    }


def achievement_axis_score(candidate: CandidateExtraction) -> tuple[float, list[str], list[dict]]:
    scored = []
    for event in scorable_achievements(candidate):
        parts = score_achievement_event(event)
        scored.append({"achievement_id": event.achievement_id, "evidence_id": event.evidence_id, "score": parts["total"], "parts": parts})
    scored.sort(key=lambda item: item["score"], reverse=True)
    neutral = [{"score": 50.0, "evidence_id": "", "achievement_id": "neutral_missing", "parts": {}} for _ in range(max(0, 3 - len(scored)))]
    top3 = (scored + neutral)[:3]
    total = 0.5 * top3[0]["score"] + 0.3 * top3[1]["score"] + 0.2 * top3[2]["score"]
    return round(clamp(total), 2), [item["evidence_id"] for item in scored[:3] if item["evidence_id"]], scored


def achievement_impact_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    score, ids, _ = achievement_axis_score(candidate)
    return score, ids
