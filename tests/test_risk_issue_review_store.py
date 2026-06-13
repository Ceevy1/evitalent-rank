from __future__ import annotations

import pytest

from evitalent.official_samples.risk_issue_review_store import ISSUE_CONFIRMED_RESOLVED, RiskIssueReviewStore, review_key


def test_risk_issue_review_store_records_anonymous_issue_decision(tmp_path):
    store = RiskIssueReviewStore(tmp_path / "risk_issue_review_records.json")

    review = store.record(
        "brand_001",
        domain="brand",
        issue="achievement 证据不足",
        decision=ISSUE_CONFIRMED_RESOLVED,
        reviewer="HR",
        note="已通过材料补充确认",
    )

    key = review_key("brand_001", "achievement 证据不足")
    assert review["document_id"] == "brand_001"
    assert store.load()["issue_reviews"][key]["review_status"] == ISSUE_CONFIRMED_RESOLVED
    assert store.summary()["resolved_issues"] == 1


def test_risk_issue_review_store_rejects_empty_issue(tmp_path):
    store = RiskIssueReviewStore(tmp_path / "risk_issue_review_records.json")

    with pytest.raises(ValueError):
        store.record("brand_001", domain="brand", issue="", decision=ISSUE_CONFIRMED_RESOLVED)
