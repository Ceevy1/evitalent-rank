from __future__ import annotations

import pytest

from evitalent.official_samples.batch_state_store import COMPLETED_ELIGIBLE, COMPLETED_NEEDS_REVIEW
from evitalent.official_samples.manual_review_store import MANUAL_APPROVED, ManualReviewStore


def test_manual_review_store_records_safe_review_decision(tmp_path):
    store = ManualReviewStore(tmp_path / "manual_review_records.json")

    review = store.record(
        "hr_001",
        domain="hr",
        source_status=COMPLETED_NEEDS_REVIEW,
        decision=MANUAL_APPROVED,
        reviewer="HR",
        note="证据链已人工确认",
    )

    assert review["document_id"] == "hr_001"
    assert store.summary()["approved_documents"] == 1
    assert store.load()["reviews"]["hr_001"]["note"] == "证据链已人工确认"


def test_manual_review_store_rejects_already_eligible_status(tmp_path):
    store = ManualReviewStore(tmp_path / "manual_review_records.json")

    with pytest.raises(ValueError):
        store.record("hr_001", domain="hr", source_status=COMPLETED_ELIGIBLE, decision=MANUAL_APPROVED)
