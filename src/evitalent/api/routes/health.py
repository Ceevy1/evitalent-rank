from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "EviTalent-Rank", "version": "1.0.0", "mode": "mock_available"}
