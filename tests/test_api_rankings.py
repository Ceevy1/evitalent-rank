def test_hr_mock_ranking_endpoint():
    from fastapi.testclient import TestClient
    from evitalent.api.main import app

    response = TestClient(app).post("/api/v1/rankings", json={"domain": "hr", "mode": "mock"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "hr"
    assert len(payload["candidates"]) >= 3
    assert "rank_score" in payload["candidates"][0]


def test_production_mock_ranking_endpoint():
    from fastapi.testclient import TestClient
    from evitalent.api.main import app

    response = TestClient(app).post("/api/v1/rankings", json={"domain": "production", "mode": "mock"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "production"
    assert len(payload["candidates"]) >= 3
    assert "rank_score" in payload["candidates"][0]


def test_real_mode_returns_stage6_message():
    from fastapi.testclient import TestClient
    from evitalent.api.main import app
    from evitalent.services.ranking_service import REAL_DOC_NOT_READY_MESSAGE

    response = TestClient(app).post("/api/v1/rankings", json={"domain": "hr", "mode": "real", "candidate_ids": ["doc_real"]})
    assert response.status_code == 422
    assert REAL_DOC_NOT_READY_MESSAGE in response.json()["detail"]
