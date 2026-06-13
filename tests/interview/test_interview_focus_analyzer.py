from __future__ import annotations

from evitalent.interview.interview_focus_analyzer import InterviewFocusAnalyzer
from evitalent.interview.models import HighFitCondition


def test_focus_analyzer_generates_required_focus_types():
    conditions = [
        HighFitCondition(condition_id="c1", label="招聘交付能力", fit_level="high", basis="已核验成果", related_event_type="recruitment_delivery", evidence_ids=["ev1"], confidence=0.9)
    ]
    analysis = {
        "achievement_events": [{"event_type": "recruitment_delivery", "metric_value": 120, "unit": "人", "evidence_id": "ev1"}],
        "risk_flags": ["证据不足"],
        "eci": 65,
    }

    focus = InterviewFocusAnalyzer().analyze(conditions, analysis)

    assert len(focus) >= 3
    assert any(item.focus_type == "strength_validation" for item in focus)
    assert any(item.focus_type == "scale_context" for item in focus)
    assert any(item.focus_type == "risk_check" for item in focus)
