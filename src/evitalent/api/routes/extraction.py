from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from evitalent.api.dependencies import get_db
from evitalent.api.schemas import ExtractionRequest
from evitalent.repositories import CandidateRepository, DocumentRepository
from evitalent.services.extraction_service import ExtractionService, ExtractionServiceError

router = APIRouter(prefix="/api/v1", tags=["extraction"])


@router.post("/resumes/{document_id}/extract")
def extract_resume(document_id: str, request: ExtractionRequest, session: Session = Depends(get_db)) -> dict:
    service = ExtractionService(DocumentRepository(session), CandidateRepository(session))
    try:
        return service.extract_document(document_id, request.mode)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="文档不存在。") from exc
    except ExtractionServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
