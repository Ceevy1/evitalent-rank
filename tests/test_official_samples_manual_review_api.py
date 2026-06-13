from __future__ import annotations

from fastapi.testclient import TestClient

from evitalent.api.main import app
from evitalent.official_samples.batch_state_store import COMPLETED_NEEDS_REVIEW
from evitalent.official_samples.manual_review_store import MANUAL_APPROVED


def test_official_samples_manual_review_api_records_decision(tmp_path, monkeypatch):
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path / "private"))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(tmp_path / "input"))
    client = TestClient(app)

    response = client.post(
        "/api/v1/official-samples/manual-review",
        json={
            "document_id": "hr_api_001",
            "domain": "hr",
            "source_status": COMPLETED_NEEDS_REVIEW,
            "decision": MANUAL_APPROVED,
            "reviewer": "HR",
            "note": "人工核验通过",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review"]["manual_status"] == MANUAL_APPROVED
    assert payload["summary"]["approved_documents"] >= 1
