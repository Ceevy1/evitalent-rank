from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from evitalent.api.dependencies import get_db
from evitalent.api.schemas import RankingRequest
from evitalent.repositories import CandidateRepository, RankingRepository
from evitalent.services.ranking_service import REAL_DOC_NOT_READY_MESSAGE, RankingService
from evitalent.services.report_service import ReportService

router = APIRouter(prefix="/api/v1", tags=["rankings"])


@router.post("/rankings")
def create_ranking(request: RankingRequest, session: Session = Depends(get_db)) -> dict:
    try:
        service = RankingService(RankingRepository(session), candidate_repository=CandidateRepository(session))
        return service.create_ranking(request.domain, request.candidate_ids, request.mode).model_dump(mode="json")
    except ValueError as exc:
        detail = str(exc) if str(exc) else REAL_DOC_NOT_READY_MESSAGE
        raise HTTPException(status_code=422, detail=detail) from exc


@router.get("/rankings/{ranking_id}")
def get_ranking(ranking_id: str, session: Session = Depends(get_db)) -> dict:
    result = RankingService(RankingRepository(session)).get_ranking(ranking_id)
    if not result:
        raise HTTPException(status_code=404, detail="排名结果不存在。")
    return result.model_dump(mode="json")


@router.get("/reports/{ranking_id}")
def get_report(ranking_id: str, session: Session = Depends(get_db)) -> dict:
    result = RankingService(RankingRepository(session)).get_ranking(ranking_id)
    if not result:
        raise HTTPException(status_code=404, detail="排名结果不存在。")
    try:
        path = ReportService().generate_ranking_report(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="报告生成失败。") from exc
    return {"ranking_id": ranking_id, "html_report_path": str(path)}
