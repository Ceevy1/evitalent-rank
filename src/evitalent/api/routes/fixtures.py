from fastapi import APIRouter, HTTPException

from evitalent.services.ranking_service import RankingService

router = APIRouter(prefix="/api/v1", tags=["fixtures"])


@router.get("/fixtures")
def list_fixtures() -> list[dict]:
    try:
        return RankingService().list_fixtures()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Fixture 校验失败，请检查 Mock 数据。") from exc
