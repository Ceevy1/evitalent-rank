from __future__ import annotations

from app.safe_view_models import build_csv_ranking_summary, build_html_ranking_summary


def test_html_and_csv_reports_do_not_include_sensitive_fields_or_values():
    rows = [
        {
            "排名": 1,
            "候选人编号": "hr_abc",
            "综合竞争力指数": 88,
            "能力表现分": 82,
            "材料可信度": 95,
            "风险扣减": 0,
            "核心优势": "招聘交付",
            "待核验事项": "",
            "有依据成果数": 3,
        }
    ]
    task = {"task_name": "HR 招聘经理分析", "domain": "hr", "job_title": "招聘经理"}
    html = build_html_ranking_summary(rows, task)
    csv = build_csv_ranking_summary(rows, task)
    combined = html + csv
    assert "本报告由人才简历综合优选系统生成" in combined
    for forbidden in ["phone", "email", "salary", "marital_status", "birth_date", "original_filename", "13900001111", "30k"]:
        assert forbidden not in combined
