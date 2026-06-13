from __future__ import annotations

import streamlit as st

COLORS = {
    "primary": "#1f3a8a",
    "primary_soft": "#eff6ff",
    "success": "#15803d",
    "warning": "#c2410c",
    "danger": "#b91c1c",
    "neutral": "#64748b",
    "border": "#dbe3ef",
    "surface": "#ffffff",
}


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 1.5rem; max-width: 1280px; }}
        div[data-testid="stMetric"] {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            padding: 14px 16px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
        }}
        .ev-card {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
            margin-bottom: 12px;
        }}
        .ev-muted {{ color: {COLORS["neutral"]}; }}
        .ev-boundary {{
            border-left: 4px solid {COLORS["primary"]};
            background: {COLORS["primary_soft"]};
            padding: 12px 14px;
            border-radius: 8px;
            margin-top: 18px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.86rem;
            font-weight: 600;
            border: 1px solid {COLORS["border"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
