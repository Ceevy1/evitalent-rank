from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from evitalent.db import DocumentRecord
from evitalent.parser.base import ParsedDocument
from evitalent.parser.docx_parser import DocxDocumentParser
from evitalent.parser.pdf_parser import PdfDocumentParser
from evitalent.privacy.redactor import RedactionResult, redact_text
from evitalent.repositories import DocumentRepository
from evitalent.settings import PROJECT_ROOT


SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


class UnsupportedDocumentType(ValueError):
    pass


class DocumentService:
    def __init__(self, repository: DocumentRepository | None = None) -> None:
        self.repository = repository

    def save_upload_bytes(self, filename: str, data: bytes) -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise UnsupportedDocumentType("仅支持 DOCX 或 PDF 文件。")
        document_id = f"doc_{uuid4().hex[:10]}"
        raw_dir = PROJECT_ROOT / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"{document_id}{suffix}"
        raw_path.write_bytes(data)

        record = DocumentRecord(
            document_id=document_id,
            source_filename=filename,
            file_type=suffix.removeprefix("."),
            parse_status="uploaded",
            raw_path=str(raw_path),
            redacted_path=None,
        )
        if self.repository:
            self.repository.add(record)
        return {
            "document_id": document_id,
            "source_filename": filename,
            "file_type": suffix.removeprefix("."),
            "parse_status": "uploaded",
            "raw_path": str(raw_path),
            "parse_url": f"/api/v1/resumes/{document_id}/parse",
        }

    async def save_upload(self, file: UploadFile) -> dict:
        return self.save_upload_bytes(file.filename or "resume.docx", await file.read())

    def parse_and_redact(self, document_id: str) -> dict:
        record = self.repository.get(document_id) if self.repository else None
        if record:
            raw_path = Path(record.raw_path)
            source_filename = record.source_filename
        else:
            matches = list((PROJECT_ROOT / "data" / "raw").glob(f"{document_id}.*"))
            if not matches:
                raise FileNotFoundError(f"文档不存在：{document_id}")
            raw_path = matches[0]
            source_filename = raw_path.name

        parsed = self._parse(raw_path)
        redaction = redact_text(parsed.cleaned_text)
        redacted_dir = PROJECT_ROOT / "data" / "redacted"
        redacted_dir.mkdir(parents=True, exist_ok=True)
        redacted_path = redacted_dir / f"{document_id}.txt"
        redacted_path.write_text(redaction.redacted_text, encoding="utf-8")

        if self.repository:
            self.repository.update_parse_result(document_id, parsed.parse_status, str(redacted_path))

        return {
            "document_id": document_id,
            "source_filename": source_filename,
            "parse_status": parsed.parse_status,
            "redacted_path": str(redacted_path),
            "redaction_completed": True,
            "redacted_preview": self._preview(redaction.redacted_text),
            "detected_pii_types": sorted(redaction.redaction_summary.keys()),
            "warnings": parsed.warnings,
        }

    def get_redacted_text(self, document_id: str) -> str:
        record = self.repository.get(document_id) if self.repository else None
        redacted_path = Path(record.redacted_path) if record and record.redacted_path else PROJECT_ROOT / "data" / "redacted" / f"{document_id}.txt"
        if not redacted_path.exists():
            raise FileNotFoundError("未找到脱敏文本，请先完成解析与脱敏。")
        return redacted_path.read_text(encoding="utf-8")

    def _parse(self, raw_path: Path) -> ParsedDocument:
        suffix = raw_path.suffix.lower()
        if suffix == ".docx":
            return DocxDocumentParser().parse(raw_path)
        if suffix == ".pdf":
            return PdfDocumentParser().parse(raw_path)
        raise UnsupportedDocumentType("仅支持 DOCX 或 PDF 文件。")

    @staticmethod
    def _preview(text: str, max_chars: int = 900) -> str:
        return text[:max_chars] + ("..." if len(text) > max_chars else "")
