from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from evitalent.api.dependencies import get_db
from evitalent.api.schemas import FairnessAuditRequest, RobustnessAuditRequest, TimelineAuditRequest
from evitalent.repositories import AuditRepository, CandidateRepository, RankingRepository
from evitalent.services.audit_service import AuditService, AuditServiceError

router = APIRouter(prefix="/api/v1", tags=["audits"])


def _service(session: Session) -> AuditService:
    return AuditService(AuditRepository(session), RankingRepository(session), CandidateRepository(session))


@router.post("/audits/timeline")
def run_timeline_audit(request: TimelineAuditRequest, session: Session = Depends(get_db)) -> dict:
    try:
        return _service(session).run_timeline(request.domain, request.candidate_ids).model_dump(mode="json")
    except AuditServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/audits/fairness")
def run_fairness_audit(request: FairnessAuditRequest, session: Session = Depends(get_db)) -> dict:
    try:
        return _service(session).run_fairness(request.ranking_id, request.audit_mode).model_dump(mode="json")
    except AuditServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/audits/robustness")
def run_robustness_audit(request: RobustnessAuditRequest, session: Session = Depends(get_db)) -> dict:
    try:
        return _service(session).run_robustness(request.ranking_id, request.audit_mode, request.top_k).model_dump(mode="json")
    except AuditServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/audits/{audit_id}")
def get_audit(audit_id: str, session: Session = Depends(get_db)) -> dict:
    result = _service(session).get_audit(audit_id)
    if not result:
        raise HTTPException(status_code=404, detail="审计结果不存在。")
    return result.model_dump(mode="json")
