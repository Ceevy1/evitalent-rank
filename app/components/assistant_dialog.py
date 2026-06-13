from __future__ import annotations

import streamlit as st

from app.components.assistant_chat_history import append_message, clear_chat_history, ensure_chat_state, render_chat_history
from app.components.assistant_quick_questions import render_quick_questions
from app.components.assistant_scope_selector import default_scope_for_page, render_scope_selector
from evitalent.assistant.chat_service import ChatService
from evitalent.assistant.models import AssistantChatRequest


def _safe_task_context() -> tuple[str | None, str | None, str | None]:
    task = st.session_state.get("tasks", {}).get(st.session_state.get("selected_task_id"))
    domain = task.get("domain") if task else st.session_state.get("selected_domain")
    return st.session_state.get("selected_task_id"), domain, st.session_state.get("selected_candidate_id")


def _mark_dialog_closed() -> None:
    st.session_state.assistant_dialog_open = False
    st.session_state.assistant_dialog_page = None


@st.dialog("人才分析助手", width="medium", on_dismiss=_mark_dialog_closed)
def render_assistant_dialog(page_name: str) -> None:
    ensure_chat_state()
    st.caption("可询问排名依据、候选人比较、待核验事项和面试建议")

    task_id, domain, candidate_id = _safe_task_context()
    picked = None
    with st.container(height=520, border=False):
        st.write(f"当前页面：{page_name}")
        st.write("数据范围：当前任务中已通过安全核验的匿名结果")
        scope = render_scope_selector(default_scope_for_page(page_name))
        if st.button("清空当前对话"):
            clear_chat_history()
            st.rerun()

        picked = render_quick_questions(page_name)
        render_chat_history()
    question = picked or st.chat_input("请输入问题，例如：解释当前排名前三的主要差异")
    if question:
        append_message("user", question)
        response = ChatService().ask(
            AssistantChatRequest(
                session_id=st.session_state.get("assistant_session_id"),
                question=question,
                scope=scope,
                task_id=task_id or "fixture_task",
                domain=domain,
                candidate_id=candidate_id,
            )
        )
        st.session_state.assistant_session_id = response.session_id
        append_message("assistant", response.answer, response.source_labels)
        # Keep the dialog open across Streamlit's rerun after chat_input submit.
        st.session_state.assistant_dialog_open = True
        st.session_state.assistant_dialog_page = page_name
        st.rerun()
    st.caption("回答用于招聘分析辅助，不构成最终录用结论。")
