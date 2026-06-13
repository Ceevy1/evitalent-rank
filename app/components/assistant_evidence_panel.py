from __future__ import annotations

import streamlit as st


def render_assistant_evidence_panel(source_labels: list[str]) -> None:
    if not source_labels:
        return
    with st.expander("查看引用依据", expanded=False):
        for label in source_labels:
            st.caption(label)
