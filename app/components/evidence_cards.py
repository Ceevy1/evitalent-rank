from __future__ import annotations

import streamlit as st


def render_evidence_cards(candidate) -> None:
    for evidence in candidate.evidence_items:
        with st.expander(f"{evidence.evidence_id} | {evidence.section} | {evidence.fact_type}"):
            st.write(evidence.quote)
            st.caption(f"用于评分：{'是' if evidence.used_for_scoring else '否'}")
