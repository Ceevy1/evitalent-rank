from __future__ import annotations

import streamlit as st


def render_candidate_scorecard(row: dict | None) -> None:
    if not row:
        st.info("请选择候选人查看详情。")
        return
    cols = st.columns(4)
    cols[0].metric("综合竞争力指数", row.get("综合竞争力指数", "-"))
    cols[1].metric("能力表现分", row.get("能力表现分", "-"))
    cols[2].metric("材料可信度", row.get("材料可信度", "-"))
    cols[3].metric("风险扣减", row.get("风险扣减", "-"))
