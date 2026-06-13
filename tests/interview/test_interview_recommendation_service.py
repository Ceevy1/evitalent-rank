from __future__ import annotations

from evitalent.interview.interview_recommendation_service import InterviewRecommendationService


def test_interview_recommendation_service_generates_complete_result():
    analysis = {
        "candidate_id": "candidate_safe_001",
        "target_domain": "hr",
        "job_title": "HRD",
        "rank_score": 82,
        "bcs": 80,
        "eci": 88,
        "penalty": 0,
        "axis_scores": {"achievement": 90, "management": 82, "competency": 78},
        "top_strengths": [{"label": "招聘交付", "score": 90}],
        "risk_flags": ["match 证据不足", "achievement 证据不足"],
        "achievement_events": [{"event_type": "recruitment_delivery", "metric_value": 120, "unit": "人", "evidence_id": "ev1"}],
        "career_records": [{"description": "负责招聘交付和团队管理", "domain_tags": ["hr"]}],
    }

    recommendation = InterviewRecommendationService().recommend(analysis)

    assert recommendation.high_fit_conditions
    assert len(recommendation.recommended_questions) >= 5
    assert all(item.why_ask and item.follow_up_probe and item.red_flags for item in recommendation.recommended_questions)
    dumped = recommendation.model_dump_json()
    assert "建议录用" not in dumped
    assert "建议淘汰" not in dumped
    assert len(recommendation.risk_verification_items) >= 2


def test_evidence_limited_candidate_gets_risk_probe():
    recommendation = InterviewRecommendationService().recommend(
        {
            "candidate_id": "candidate_safe_002",
            "target_domain": "ecommerce",
            "eci": 50,
            "axis_scores": {},
            "risk_flags": [],
            "achievement_events": [],
            "career_records": [],
        }
    )

    assert any(item.question_type == "risk_probe" for item in recommendation.recommended_questions)
