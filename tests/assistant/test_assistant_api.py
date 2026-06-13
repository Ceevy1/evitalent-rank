from __future__ import annotations

from fastapi.testclient import TestClient

from evitalent.api.main import app


def test_assistant_api_status_index_and_chat_safe():
    client = TestClient(app)
    status = client.get("/api/v1/assistant/status")
    assert status.status_code == 200
    assert "api_key" not in status.text.lower()

    official = client.post("/api/v1/assistant/index/rebuild", params={"scope": "official_safe_results"})
    assert official.status_code == 400

    rebuilt = client.post("/api/v1/assistant/index/rebuild", params={"scope": "fixture_safe_data"})
    assert rebuilt.status_code == 200
    assert rebuilt.json()["safety_passed"] is True

    chat = client.post(
        "/api/v1/assistant/chat",
        json={"question": "综合竞争力指数如何计算？", "scope": "system_help", "task_id": "fixture_task", "domain": "hr"},
    )
    assert chat.status_code == 200
    assert "13900001111" not in chat.text
