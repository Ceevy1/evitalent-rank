from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from evitalent.api.main import app
from evitalent.settings import PROJECT_ROOT


def test_audit_api_endpoints_and_schema():
    client = TestClient(app)
    ranking = client.post("/api/v1/rankings", json={"domain": "hr", "mode": "mock"}).json()
    ranking_id = ranking["ranking_id"]

    timeline = client.post("/api/v1/audits/timeline", json={"domain": "hr"}).json()
    fairness = client.post("/api/v1/audits/fairness", json={"ranking_id": ranking_id}).json()
    robustness = client.post("/api/v1/audits/robustness", json={"ranking_id": ranking_id, "top_k": 3}).json()

    schema = __import__("json").loads((PROJECT_ROOT / "schemas" / "audit_result.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for payload in (timeline, fairness, robustness):
        assert not list(validator.iter_errors(payload))
        dumped = __import__("json").dumps(payload, ensure_ascii=False)
        assert "13812345678" not in dumped
        assert "20k" not in dumped.lower()

    get_response = client.get(f"/api/v1/audits/{fairness['audit_id']}")
    assert get_response.status_code == 200
