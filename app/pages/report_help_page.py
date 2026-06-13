from __future__ import annotations

import streamlit as st

from app.components.report_download_panel import render_report_download_panel
from app.components.technical_acceptance_expander import render_technical_acceptance_expander
from app.safe_view_models import load_safe_workspace, official_ranking_rows
from app.ui_copy import DOMAIN_LABELS, REPORT_BOUNDARY_NOTICE
from app.ui_state import current_task, init_session_state


def render() -> None:
    init_session_state()
    st.title("报告导出与系统说明")
    task = current_task()
    domain = task.get("domain") if task else st.selectbox("评价领域", list(DOMAIN_LABELS), format_func=lambda key: DOMAIN_LABELS[key])
    rows = official_ranking_rows(load_safe_workspace(), domain)
    st.markdown("### 当前任务摘要")
    st.write(task or "尚未创建分析任务，请先创建一个岗位分析任务。")
    st.markdown("### 排名结果摘要")
    render_report_download_panel(rows, task)
    st.info(REPORT_BOUNDARY_NOTICE)
    with st.expander("方法说明", expanded=False):
        st.write("综合竞争力指数由能力表现分、材料可信度与风险扣减共同形成。材料缺失不会被直接判零，但会影响材料可信度。")
        st.write("系统只使用已通过隐私处理和成果依据核验的信息，不使用姓名、婚姻、薪资等敏感字段。")
    render_technical_acceptance_expander()
