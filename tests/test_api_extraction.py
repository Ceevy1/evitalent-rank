import json

from fastapi.testclient import TestClient

from evitalent.api.main import app
from evitalent.settings import PROJECT_ROOT
from scripts.generate_demo_resume_files import main as generate_demo_files


def _fixture_payload(candidate_id="candidate_api_llm"):
    payload = json.loads((PROJECT_ROOT / "data" / "fixtures" / "extracted" / "demo_hr_001.json").read_text(encoding="utf-8"))
    payload["document_id"] = "doc_api_llm"
    payload["candidate_id"] = candidate_id
    return payload


def _upload_demo_docx(client: TestClient) -> str:
    generate_demo_files()
    path = PROJECT_ROOT / "data" / "fixtures" / "source_documents" / "demo_hr_resume.docx"
    with path.open("rb") as fh:
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("demo_hr_resume.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 200
    return response.json()["document_id"]


def test_api_extraction_mock_mode_works():
    client = TestClient(app)
    response = client.post("/api/v1/resumes/demo_hr_001/extract", json={"mode": "mock"})
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_id"] == "demo_hr_001"
    assert data["eligible_for_scoring"] is True


def test_api_extraction_rejects_unredacted_uploaded_document(monkeypatch):
    client = TestClient(app)
    document_id = _upload_demo_docx(client)
    response = client.post(f"/api/v1/resumes/{document_id}/extract", json={"mode": "local_ollama"})
    assert response.status_code == 422
    assert "脱敏" in response.json()["detail"]


def test_api_extraction_with_mocked_llm_then_extracted_ranking(monkeypatch):
    class FakeLLMClient:
        model = "fake-model"
        temperature = 0

        def __init__(self, *args, **kwargs):
            pass

        def generate_json(self, system_prompt, user_prompt):
            assert "脱敏简历文本" in user_prompt
            assert "13812345678" not in user_prompt
            return _fixture_payload("candidate_api_llm")

    monkeypatch.setattr("evitalent.services.extraction_service.LLMClient", FakeLLMClient)

    client = TestClient(app)
    document_id = _upload_demo_docx(client)
    parse_response = client.post(f"/api/v1/resumes/{document_id}/parse")
    assert parse_response.status_code == 200

    extract_response = client.post(f"/api/v1/resumes/{document_id}/extract", json={"mode": "local_ollama"})
    assert extract_response.status_code == 200
    extract_data = extract_response.json()
    assert extract_data["candidate_id"] == "candidate_api_llm"
    assert extract_data["eligible_for_scoring"] is True

    ranking_response = client.post(
        "/api/v1/rankings",
        json={"domain": "hr", "candidate_ids": ["candidate_api_llm"], "mode": "extracted"},
    )
    assert ranking_response.status_code == 200
    assert ranking_response.json()["candidates"][0]["rank_score"] > 0
