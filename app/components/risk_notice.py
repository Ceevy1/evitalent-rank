from __future__ import annotations

import streamlit as st

from app.ui_copy import BOUNDARY_NOTICE, STATUS_HELP


def render_boundary_notice() -> None:
    st.markdown(f"<div class='ev-boundary'>{BOUNDARY_NOTICE}</div>", unsafe_allow_html=True)


def render_status_help(status: str) -> None:
    if status in STATUS_HELP:
        st.warning(STATUS_HELP[status])
