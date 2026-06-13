from __future__ import annotations

import streamlit as st

from app.page_navigation import switch_to_page
from app.ui_copy import DOMAIN_FOCUS, DOMAIN_LABELS, is_template_domain
from app.ui_state import create_task, init_session_state


def render() -> None:
    init_session_state()
    st.title("新建分析任务")
    domain = st.radio(
        "评价领域",
        list(DOMAIN_LABELS),
        format_func=lambda key: DOMAIN_LABELS[key],
        horizontal=True,
        key="create_task_domain",
    )
    st.markdown("**当前领域重点能力**")
    st.write("、".join(DOMAIN_FOCUS[domain]))
    if is_template_domain(domain):
        st.warning("当前领域采用 V1 模板评价规则，后续仍可结合更多专家标注进一步校准。")
    with st.form("create_task_form"):
        task_name = st.text_input("任务名称")
        job_title = st.text_input("岗位名称")
        focus = st.text_area("分析重点", placeholder="可填写该岗位特别关注的经验、成果或管理能力。")
        st.info("本次分析使用固定 V1 评价规则，不因候选人结果自动调整评分权重。")
        privacy_ok = st.checkbox("我了解系统将先对简历进行隐私保护处理，再进行智能分析。")
        submitted = st.form_submit_button("创建任务")
    if submitted:
        if not task_name or not job_title or not privacy_ok:
            st.error("请填写任务名称、岗位名称，并确认隐私处理说明。")
            return
        create_task(task_name, domain, job_title, focus)
        st.success("分析任务已创建，请继续导入简历并完成隐私检查。")
        switch_to_page("privacy_check")
