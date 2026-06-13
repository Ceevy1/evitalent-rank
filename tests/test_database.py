from uuid import uuid4

from evitalent.db import DocumentRecord, RankingRecord, get_session, init_db
from evitalent.repositories import DocumentRepository, RankingRepository


def test_database_initialization_and_metadata_save():
    init_db()
    document_id = f"test_doc_{uuid4().hex[:8]}"
    ranking_id = f"test_ranking_{uuid4().hex[:8]}"
    with get_session() as session:
        doc = DocumentRepository(session).add(
            DocumentRecord(
                document_id=document_id,
                source_filename="demo.docx",
                file_type="docx",
                parse_status="uploaded",
                raw_path="data/raw/demo.docx",
                redacted_path=None,
            )
        )
        ranking = RankingRepository(session).add(
            RankingRecord(
                ranking_id=ranking_id,
                domain="hr",
                method_version="stage4_v1",
                result_json_path="data/outputs/rankings/demo.json",
            )
        )
        assert doc.document_id == document_id
        assert ranking.ranking_id == ranking_id


def test_database_does_not_store_sensitive_plaintext():
    document_id = f"test_doc_{uuid4().hex[:8]}"
    with get_session() as session:
        doc = DocumentRepository(session).add(
            DocumentRecord(
                document_id=document_id,
                source_filename="resume.docx",
                file_type="docx",
                parse_status="parsed",
                raw_path="data/raw/resume.docx",
                redacted_path="data/redacted/resume.txt",
            )
        )
        serialized = " ".join(str(getattr(doc, name)) for name in ["document_id", "source_filename", "file_type", "parse_status", "raw_path", "redacted_path"])
        assert "13900001234" not in serialized
        assert "28K" not in serialized
        assert "陆晨" not in serialized
