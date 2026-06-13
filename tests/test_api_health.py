def test_health_endpoint():
    from fastapi.testclient import TestClient
    from evitalent.api.main import app

    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "EviTalent-Rank"
    assert payload["version"] == "1.0.0"
    assert payload["status"] == "ok"
