from __future__ import annotations

from pathlib import Path


def test_official_dataset_pipeline_script_uses_project_dataset_and_exports_safe_outputs():
    source = Path("scripts/run_official_dataset_analysis.py").read_text(encoding="utf-8")
    assert "data\" / \"raw\" / \"resumes" in source
    assert "OfficialInventoryService" in source
    assert "confirm_redaction_review" in source
    assert "OfficialBatchExtractionRunner" in source
    assert "DomainRankingRunner" in source
    assert "build_safe_html_report" in source
    assert "candidate_extraction" in source


def test_official_dataset_frontend_has_six_domain_visualization():
    source = Path("app/pages/analysis_history_page.py").read_text(encoding="utf-8")
    assert "主办方数据集六领域分析可视化" in source
    assert "_dataset_coverage_chart" in source
    assert "_domain_score_chart" in source
    assert "最高综合竞争力指数" in source
