from __future__ import annotations

from app.ui_copy import STATUS_HELP, STATUS_LABELS, DOMAIN_FOCUS, is_template_domain


def test_business_status_mapping_covers_required_statuses():
    required = [
        "completed_eligible",
        "completed_needs_review",
        "failed_redaction",
        "failed_schema",
        "failed_grounding",
        "failed_safety",
        "failed_model_request",
        "domain_mismatch_needs_review",
    ]
    for status in required:
        assert status in STATUS_LABELS
        assert not STATUS_LABELS[status].startswith(status)


def test_exception_help_and_template_domain_notice_inputs():
    assert "暂不纳入正式排序" in STATUS_HELP["failed_grounding"]
    assert is_template_domain("sales") is True
    assert is_template_domain("rd") is True
    assert "专利成果" in DOMAIN_FOCUS["rd"]
