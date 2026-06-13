from __future__ import annotations

import streamlit as st

from app.ui_copy import label_for_status

STATUS_COLOR = {
    "completed_eligible": ("#dcfce7", "#166534"),
    "completed_needs_review": ("#ffedd5", "#9a3412"),
    "failed_redaction": ("#fee2e2", "#991b1b"),
    "failed_grounding": ("#fee2e2", "#991b1b"),
    "failed_safety": ("#fee2e2", "#991b1b"),
    "failed_model_request": ("#f1f5f9", "#475569"),
    "pending": ("#f1f5f9", "#475569"),
    "processing": ("#dbeafe", "#1d4ed8"),
}


def render_status_badge(status: str) -> None:
    bg, fg = STATUS_COLOR.get(status, ("#f1f5f9", "#475569"))
    st.markdown(
        f"<span class='status-badge' style='background:{bg};color:{fg}'>{label_for_status(status)}</span>",
        unsafe_allow_html=True,
    )
