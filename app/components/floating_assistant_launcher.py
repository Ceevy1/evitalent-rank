from __future__ import annotations

import streamlit as st

from app.components.assistant_dialog import render_assistant_dialog


def render_floating_assistant_launcher(page_name: str) -> None:
    st.session_state.setdefault("assistant_dialog_open", False)
    st.session_state.setdefault("assistant_dialog_page", None)
    if (
        st.session_state.assistant_dialog_open
        and st.session_state.assistant_dialog_page is not None
        and st.session_state.assistant_dialog_page != page_name
    ):
        st.session_state.assistant_dialog_open = False
        st.session_state.assistant_dialog_page = None

    st.markdown(
        """
        <style>
        .st-key-floating_ai_launcher {
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 9999;
            max-width: 180px;
        }
        .st-key-floating_ai_launcher button {
            border-radius: 999px;
            background: #1f3a8a;
            color: white;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
            border: 0;
        }
        @media (max-width: 720px) {
            .st-key-floating_ai_launcher { right: 12px; bottom: 12px; max-width: 140px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="floating_ai_launcher"):
        if st.button("💬 AI 助手", use_container_width=True):
            st.session_state.assistant_dialog_open = True
            st.session_state.assistant_dialog_page = page_name

    if st.session_state.assistant_dialog_open and st.session_state.assistant_dialog_page == page_name:
        render_assistant_dialog(page_name)
