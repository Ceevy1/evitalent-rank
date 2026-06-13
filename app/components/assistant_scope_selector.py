from __future__ import annotations

import streamlit as st

from evitalent.assistant.models import ContextScope

SCOPE_LABELS = {
    ContextScope.system_help: "系统使用与评分规则",
    ContextScope.current_candidate: "当前候选人",
    ContextScope.current_task: "当前分析任务",
    ContextScope.current_domain: "当前领域安全结果",
}


def default_scope_for_page(page_name: str) -> ContextScope:
    if page_name in {"工作台首页", "新建分析任务", "简历导入与隐私检查"}:
        return ContextScope.system_help
    if page_name == "候选人详情":
        return ContextScope.current_candidate
    return ContextScope.current_task


def render_scope_selector(default_scope: ContextScope) -> ContextScope:
    return st.selectbox("数据范围", list(SCOPE_LABELS), index=list(SCOPE_LABELS).index(default_scope), format_func=lambda scope: SCOPE_LABELS[scope])
