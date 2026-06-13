from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi.testclient import TestClient

from evitalent.api.main import app


def main() -> None:
    client = TestClient(app)
    health = client.get("/api/v1/health")
    fixtures = client.get("/api/v1/fixtures")
    ranking = client.post("/api/v1/rankings", json={"domain": "hr", "mode": "mock"})
    print({"health_status": health.status_code, "health": health.json()})
    print({"fixtures_status": fixtures.status_code, "fixture_count": len(fixtures.json())})
    print({"ranking_status": ranking.status_code, "ranking_id": ranking.json().get("ranking_id"), "candidate_count": len(ranking.json().get("candidates", []))})


if __name__ == "__main__":
    main()
