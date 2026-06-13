from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from evitalent.api.dependencies import get_db
from evitalent.repositories import DocumentRepository
from evitalent.services.document_service import DocumentService, UnsupportedDocumentType

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), session: Session = Depends(get_db)) -> dict:
    try:
        service = DocumentService(DocumentRepository(session))
        payload = await service.save_upload(file)
        return {
            "document_id": payload["document_id"],
            "source_filename": payload["source_filename"],
            "file_type": payload["file_type"],
            "parse_status": payload["parse_status"],
            "parse_url": payload["parse_url"],
        }
    except UnsupportedDocumentType as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{document_id}/parse")
def parse_resume(document_id: str, session: Session = Depends(get_db)) -> dict:
    try:
        service = DocumentService(DocumentRepository(session))
        payload = service.parse_and_redact(document_id)
        return {
            "document_id": payload["document_id"],
            "parse_status": payload["parse_status"],
            "redacted_preview": payload["redacted_preview"],
            "detected_pii_types": payload["detected_pii_types"],
            "warnings": payload["warnings"],
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="文档不存在。") from exc
    except UnsupportedDocumentType as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
