from __future__ import annotations

from pathlib import Path


def test_page_registry_contains_all_workflow_pages():
    source = Path("app/streamlit_app.py").read_text(encoding="utf-8")
    for key in [
        "create_task",
        "privacy_check",
        "processing_status",
        "ranking",
        "candidate_detail",
        "analysis_history",
        "report_help",
    ]:
        assert f'"{key}"' in source
    assert "register_pages(page_registry)" in source


def test_workflow_buttons_switch_to_next_stage():
    expected = {
        "app/pages/home_page.py": ['switch_to_page("create_task")', 'switch_to_page("ranking")'],
        "app/pages/create_task_page.py": ['switch_to_page("privacy_check")'],
        "app/pages/upload_privacy_page.py": ['switch_to_page("processing_status")'],
        "app/pages/processing_status_page.py": ['switch_to_page("ranking")'],
        "app/pages/ranking_page.py": ['switch_to_page("candidate_detail")'],
    }
    for file_name, snippets in expected.items():
        source = Path(file_name).read_text(encoding="utf-8")
        assert "请从左侧导航" not in source
        for snippet in snippets:
            assert snippet in source
