from __future__ import annotations

from pathlib import Path


def test_upload_page_runs_real_redaction_instead_of_demo_warning():
    source = Path("app/pages/upload_privacy_page.py").read_text(encoding="utf-8")
    assert "DocumentService" in source
    assert "save_upload_bytes" in source
    assert "parse_and_redact" in source
    assert "redacted_document_rows_by_task" in source
    assert "resume_upload_{task_id}" in source
    assert "本页面演示上传入口" not in source


def test_processing_page_runs_extraction_and_ranking():
    source = Path("app/pages/processing_status_page.py").read_text(encoding="utf-8")
    assert "ExtractionService" in source
    assert "RankingService" in source
    assert "extract_document" in source
    assert "create_ranking" in source
    assert "mode=\"extracted\"" in source
    assert "uploaded_document_ids_by_task" in source
    assert "extracted_candidate_ids_by_task" in source
    assert "task_ranking_ids" in source


def test_ranking_page_can_read_only_current_task_generated_ranking():
    ranking_page = Path("app/pages/ranking_page.py").read_text(encoding="utf-8")
    assert "task_ranking_ids" in ranking_page
    assert "ranking_id=ranking_id" in ranking_page

    source = Path("app/safe_view_models.py").read_text(encoding="utf-8")
    assert "local_ranking_rows" in source
    assert "data\" / \"outputs\" / \"rankings" in source
    assert "if ranking_id" in source
    assert "return []" in source
