from __future__ import annotations

from evitalent.official_samples.batch_state_store import COMPLETED_ELIGIBLE, FAILED_MODEL_REQUEST, BatchStateStore


def test_batch_state_store_records_resume_and_failures(tmp_path):
    store = BatchStateStore(tmp_path / "state.json")
    records = [
        {"document_id": "hr_a", "folder_domain": "hr"},
        {"document_id": "hr_b", "folder_domain": "hr"},
    ]
    store.initialize(records)
    store.mark("hr_a", COMPLETED_ELIGIBLE, result_path="x.json")
    store.mark("hr_b", FAILED_MODEL_REQUEST, error_type="LLMClientError")

    resumed = store.initialize(records, resume=True)
    assert resumed["documents"]["hr_a"]["status"] == COMPLETED_ELIGIBLE
    assert resumed["documents"]["hr_b"]["status"] == FAILED_MODEL_REQUEST
    assert store.is_final("hr_a") is True
