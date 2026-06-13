from __future__ import annotations

from app.ui_state import can_start_analysis, official_review_confirmed


def test_redaction_review_required_before_analysis():
    rows = [{"safety_passed": True, "review_confirmed": False}]
    assert can_start_analysis(rows) is False
    rows[0]["review_confirmed"] = True
    assert can_start_analysis(rows) is True


def test_official_review_gate_status():
    assert official_review_confirmed(None) is False
    assert official_review_confirmed({"review_confirmed": False}) is False
    assert official_review_confirmed({"review_confirmed": True}) is True
