from __future__ import annotations

import streamlit as st

from app.ui_copy import BOUNDARY_NOTICE, label_for_domain


def render_task_header(task: dict | None) -> None:
    if not task:
        st.info("尚未创建分析任务，请先创建一个岗位分析任务。")
        return
    st.caption("当前分析任务")
    st.title(task.get("task_name", "未命名分析任务"))
    st.write(f"岗位：{task.get('job_title', '未填写')} ｜ 评价领域：{label_for_domain(task.get('domain'))}")
    if task.get("focus"):
        st.caption(f"分析重点：{task['focus']}")
    st.markdown(f"<div class='ev-boundary'>{BOUNDARY_NOTICE}</div>", unsafe_allow_html=True)
