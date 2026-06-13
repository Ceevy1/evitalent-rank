from __future__ import annotations

from pathlib import Path


def test_ranking_page_exposes_risk_issue_review_panel():
    ranking_page = Path("app/pages/ranking_page.py").read_text(encoding="utf-8")
    panel = Path("app/components/risk_issue_review_panel.py").read_text(encoding="utf-8")

    assert "render_risk_issue_review_panel" in ranking_page
    assert "risk_issue_review_rows" in ranking_page
    assert "RiskIssueReviewStore" in panel
    assert "保存事项处理结果" in panel
    assert "不会修改评分权重、RankScore 或原始简历" in panel
