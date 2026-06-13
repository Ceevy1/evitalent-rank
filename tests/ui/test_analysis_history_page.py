from __future__ import annotations

from pathlib import Path


def test_analysis_history_page_is_registered_in_sidebar_navigation():
    app_source = Path("app/streamlit_app.py").read_text(encoding="utf-8")
    assert "analysis_history_page" in app_source
    assert 'title="分析历史记录"' in app_source
    assert 'url_path="analysis-history"' in app_source


def test_analysis_history_page_shows_safe_task_details():
    source = Path("app/pages/analysis_history_page.py").read_text(encoding="utf-8")
    assert "分析历史记录" in source
    assert "任务详细数据" in source
    assert "分析过程明细" in source
    assert "排名结果明细" in source
    assert "load_safe_workspace" in source
    assert "原始简历" not in source
