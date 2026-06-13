from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.comparison_charts import bcs_eci_grouped_bar, radar_compare_chart, rankscore_bar_chart
from app.components.metric_cards import render_metric_cards
from app.components.risk_issue_review_panel import render_risk_issue_review_panel
from app.components.scrollable_plotly import render_scrollable_plotly_chart
from app.page_navigation import switch_to_page
from app.components.task_header import render_task_header
from app.safe_view_models import attach_risk_issue_review_status, load_safe_workspace, official_ranking_rows, risk_issue_review_rows
from app.ui_copy import DOMAIN_LABELS, label_for_domain
from app.ui_state import current_task, init_session_state, set_selected_candidate


def render() -> None:
    init_session_state()
    task = current_task()
    render_task_header(task)
    st.title("人才排名与对比")
    domain = task.get("domain") if task else st.selectbox("评价领域", list(DOMAIN_LABELS), format_func=lambda key: DOMAIN_LABELS[key])
    ranking_id = st.session_state.task_ranking_ids.get(task["task_id"]) if task else None
    workspace = load_safe_workspace()
    rows = attach_risk_issue_review_status(official_ranking_rows(workspace, domain, ranking_id=ranking_id), workspace)
    st.write(f"评价领域：{label_for_domain(domain)}")
    st.caption("排序仅在当前岗位方向的可比较候选人范围内生成。")
    if not rows:
        st.info("当前还没有可查看的排名结果，请先完成简历分析。")
        return
    render_metric_cards(
        {
            "第一名综合竞争力指数": rows[0].get("综合竞争力指数", 0),
            "平均材料可信度": round(sum(float(row.get("材料可信度", 0)) for row in rows) / len(rows), 2),
            "待核验候选人数": sum(1 for row in rows if int(row.get("_pending_risk_issue_count", 0)) > 0),
            "有依据成果总数": sum(int(row.get("有依据成果数", 0)) for row in rows),
        }
    )
    filter_risk = st.checkbox("只看仍有未处理待核验事项的候选人")
    shown = [row for row in rows if int(row.get("_pending_risk_issue_count", 0)) > 0] if filter_risk else rows
    public_shown = [{key: value for key, value in row.items() if not str(key).startswith("_")} for row in shown]
    st.dataframe(pd.DataFrame(public_shown), hide_index=True, use_container_width=True)
    render_risk_issue_review_panel(risk_issue_review_rows(shown, workspace, domain))
    render_scrollable_plotly_chart(rankscore_bar_chart(shown), item_count=len(shown), height=360)
    render_scrollable_plotly_chart(bcs_eci_grouped_bar(shown), item_count=len(shown), height=360)
    selected = st.multiselect("选择 2 至 3 名候选人进行雷达图对比", [row["候选人编号"] for row in shown], max_selections=3)
    if len(selected) >= 2:
        render_scrollable_plotly_chart(
            radar_compare_chart([row for row in shown if row["候选人编号"] in selected]),
            item_count=len(selected),
            height=420,
            viewport_width=720,
            min_chart_width=640,
            per_item_width=180,
        )
    detail = st.selectbox("查看候选人详情", [row["候选人编号"] for row in rows])
    if st.button("查看详情"):
        set_selected_candidate(detail)
        switch_to_page("candidate_detail")
