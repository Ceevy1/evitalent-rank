from __future__ import annotations

import streamlit as st


def render_metric_cards(metrics: dict[str, int | float | str]) -> None:
    columns = st.columns(max(1, min(4, len(metrics))))
    for column, (label, value) in zip(columns, metrics.items()):
        column.metric(label, value)
