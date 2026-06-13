from __future__ import annotations

from pathlib import Path


def test_task_scoped_analysis_state_defaults_and_create_task_reset():
    source = Path("app/ui_state.py").read_text(encoding="utf-8")
    assert "uploaded_document_ids_by_task" in source
    assert "redacted_document_rows_by_task" in source
    assert "analysis_processing_rows_by_task" in source
    assert "extracted_candidate_ids_by_task" in source
    assert "task_ranking_ids" in source
    assert "st.session_state.selected_ranking_id = None" in source
    assert "setdefault(task_id, [])" in source
