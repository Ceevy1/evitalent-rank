from __future__ import annotations

from evitalent.interview.competency_matcher import CompetencyMatcher


def _analysis(domain: str, event_type: str, eci: float = 90) -> dict:
    return {
        "target_domain": domain,
        "axis_scores": {"achievement": 88, "competency": 80, "management": 75},
        "top_strengths": [],
        "normalized_achievement_events": [{"event_type": event_type, "evidence_id": "ev1", "metric_value": 10}],
        "career_records": [{"description": "负责团队管理，推动业务提升。", "domain_tags": [domain]}],
        "eci": eci,
    }


def test_hr_recruitment_event_matches_delivery_competency():
    conditions = CompetencyMatcher().match(_analysis("hr", "recruitment_delivery"))
    assert any("招聘交付" in item.label for item in conditions)


def test_production_loss_reduction_matches_cost_improvement():
    conditions = CompetencyMatcher().match(_analysis("production", "loss_reduction"))
    assert any("损耗" in item.label or "成本" in item.label for item in conditions)


def test_ecommerce_gmv_matches_growth_competency():
    conditions = CompetencyMatcher().match(_analysis("ecommerce", "gmv_growth"))
    assert any("增长" in item.label for item in conditions)


def test_low_evidence_result_is_not_high_fit():
    conditions = CompetencyMatcher().match(_analysis("hr", "recruitment_delivery", eci=20))
    event_condition = next(item for item in conditions if "招聘交付" in item.label)
    assert event_condition.fit_level != "high"
