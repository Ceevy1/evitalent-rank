from __future__ import annotations

import streamlit as st

from app.components.metric_cards import render_metric_cards
from app.page_navigation import switch_to_page
from app.components.risk_notice import render_boundary_notice
from app.safe_view_models import load_safe_workspace, overview_metrics
from app.ui_copy import DOMAIN_LABELS
from app.ui_state import init_session_state


def render() -> None:
    init_session_state()
    workspace = load_safe_workspace()
    st.title("人才简历综合优选系统")
    st.subheader("帮助 HR 快速识别候选人的相关经验、核心成果与岗位竞争力")
    col1, col2 = st.columns(2)
    if col1.button("新建分析任务", use_container_width=True):
        switch_to_page("create_task")
    if col2.button("查看已有结果", use_container_width=True):
        switch_to_page("ranking")

    st.markdown("### 工作台概览")
    render_metric_cards(overview_metrics(workspace))
    if not any(overview_metrics(workspace).values()):
        st.info("尚未创建分析任务，请先创建一个岗位分析任务。")

    st.markdown("### 支持的评价领域")
    cols = st.columns(3)
    for index, label in enumerate(DOMAIN_LABELS.values()):
        cols[index % 3].markdown(f"<div class='ev-card'><strong>{label}</strong><br><span class='ev-muted'>同领域候选人对比分析</span></div>", unsafe_allow_html=True)

    st.markdown("### 五步流程")
    st.write("导入简历 → 隐私保护 → 智能分析 → 对比排序 → 导出报告")
    render_boundary_notice()
