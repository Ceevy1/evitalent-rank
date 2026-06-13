from __future__ import annotations

import streamlit as st

from app.safe_view_models import build_csv_ranking_summary, build_html_ranking_summary


def render_report_download_panel(rows: list[dict], task: dict | None) -> None:
    if not rows:
        st.info("当前还没有可导出的排名结果，请先完成简历分析。")
        return
    html_report = build_html_ranking_summary(rows, task)
    csv_report = build_csv_ranking_summary(rows, task)
    st.download_button("导出 HTML 分析报告", data=html_report, file_name="talent_ranking_safe_report.html", mime="text/html")
    st.download_button("导出 CSV 排名摘要", data=csv_report, file_name="talent_ranking_safe_summary.csv", mime="text/csv")
    st.caption("报告仅包含匿名编号和分数摘要，不包含联系方式、婚姻、薪资或原始简历全文。")
