from __future__ import annotations

from pathlib import Path


def test_processing_page_shows_progress_feedback_during_analysis():
    source = Path("app/pages/processing_status_page.py").read_text(encoding="utf-8")
    assert "st.status" in source
    assert "st.progress" in source
    assert "update_progress" in source
    assert "正在调用 Ollama 抽取匿名简历" in source
    assert "结构化分析完成，正在生成当前岗位方向的排序结果" in source
    assert "智能分析与排序已完成" in source
    assert "st.toast" in source
