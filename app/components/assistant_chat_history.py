from __future__ import annotations

import streamlit as st


def ensure_chat_state() -> None:
    st.session_state.setdefault("assistant_messages", [])
    st.session_state.setdefault("assistant_session_id", None)


def render_chat_history() -> None:
    ensure_chat_state()
    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("source_labels"):
                with st.expander("查看引用依据", expanded=False):
                    for label in message["source_labels"]:
                        st.caption(label)


def append_message(role: str, content: str, source_labels: list[str] | None = None) -> None:
    ensure_chat_state()
    st.session_state.assistant_messages.append({"role": role, "content": content, "source_labels": source_labels or []})


def clear_chat_history() -> None:
    st.session_state.assistant_messages = []
