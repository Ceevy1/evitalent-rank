from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.candidate_scorecard import render_candidate_scorecard
from app.components.evidence_card import render_evidence_table
from app.components.interview_focus_panel import render_interview_focus_panel
from app.components.risk_notice import render_boundary_notice
from app.safe_view_models import load_safe_workspace, official_ranking_rows
from app.ui_copy import DOMAIN_LABELS
from app.ui_state import current_task, init_session_state


def render() -> None:
    init_session_state()
    st.title("候选人详情")
    task = current_task()
    domain = task.get("domain") if task else st.selectbox("评价领域", list(DOMAIN_LABELS), format_func=lambda key: DOMAIN_LABELS[key])
    rows = official_ranking_rows(load_safe_workspace(), domain)
    if not rows:
        st.info("当前还没有可查看的候选人详情，请先完成简历分析。")
        return
    selected = st.session_state.get("selected_candidate_id") or rows[0]["候选人编号"]
    selected = st.selectbox("候选人编号", [row["候选人编号"] for row in rows], index=[row["候选人编号"] for row in rows].index(selected) if selected in [row["候选人编号"] for row in rows] else 0)
    row = next((item for item in rows if item["候选人编号"] == selected), None)
    render_candidate_scorecard(row)
    render_boundary_notice()
    st.markdown("### 核心优势")
    st.write(row.get("核心优势") or "安全摘要中暂无核心优势标签。")
    st.markdown("### 成果证据表格")
    render_evidence_table(
        [
            {
                "成果类别": "有依据成果",
                "成果描述": "安全摘要仅展示成果数量，私有证据片段默认不展示。",
                "数值": row.get("有依据成果数", 0),
                "依据状态": "已核验",
                "是否计分": "是",
            }
        ]
    )
    st.markdown("### 工作经历时间线")
    st.info("安全摘要中不包含完整经历时间线。需要详情时请通过受控服务读取最小必要脱敏片段。")
    st.markdown("### 待核验事项")
    st.write(row.get("待核验事项") or "暂无明显待核验事项。")
    render_interview_focus_panel(row, domain, task.get("job_title", "") if task else "")
