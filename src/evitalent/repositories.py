from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from evitalent.db import AuditRecord, CandidateRecord, DocumentRecord, RankingRecord


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: DocumentRecord) -> DocumentRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, document_id: str) -> DocumentRecord | None:
        return self.session.query(DocumentRecord).filter_by(document_id=document_id).one_or_none()

    def update_parse_result(self, document_id: str, parse_status: str, redacted_path: str | None) -> DocumentRecord | None:
        record = self.get(document_id)
        if record:
            record.parse_status = parse_status
            record.redacted_path = redacted_path
            self.session.commit()
            self.session.refresh(record)
        return record


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: CandidateRecord) -> CandidateRecord:
        existing = self.get(record.candidate_id)
        if existing:
            existing.document_id = record.document_id
            existing.masked_display_name = record.masked_display_name
            existing.extraction_json_path = record.extraction_json_path
            existing.extraction_mode = record.extraction_mode
            self.session.commit()
            self.session.refresh(existing)
            return existing
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, candidate_id: str) -> CandidateRecord | None:
        return self.session.query(CandidateRecord).filter_by(candidate_id=candidate_id).one_or_none()

    def list_by_ids(self, candidate_ids: list[str] | None = None) -> list[CandidateRecord]:
        query = self.session.query(CandidateRecord)
        if candidate_ids:
            query = query.filter(CandidateRecord.candidate_id.in_(candidate_ids))
        return list(query.all())


class RankingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: RankingRecord) -> RankingRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, ranking_id: str) -> RankingRecord | None:
        return self.session.query(RankingRecord).filter_by(ranking_id=ranking_id).one_or_none()


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: AuditRecord) -> AuditRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get(self, audit_id: str) -> AuditRecord | None:
        return self.session.query(AuditRecord).filter_by(audit_id=audit_id).one_or_none()
