from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.charts import career_timeline, radar_chart
from app.components.evidence_cards import render_evidence_cards


def render_candidate_detail(candidate, ranking_item) -> None:
    cols = st.columns(3)
    cols[0].metric("BCS", f"{ranking_item.bcs:.2f}")
    cols[1].metric("ECI", f"{ranking_item.eci:.2f}")
    cols[2].metric("RankScore", f"{ranking_item.rank_score:.2f}")

    st.plotly_chart(radar_chart(ranking_item.axis_scores, ranking_item.candidate_id), use_container_width=True)

    st.subheader("计算特征摘要")
    feature_items = [{"feature": key, "value": value} for key, value in ranking_item.computed_features.items() if key != "achievement_event_scores"]
    st.dataframe(pd.DataFrame(feature_items), hide_index=True, use_container_width=True)

    st.subheader("Top strengths")
    st.dataframe(pd.DataFrame([s.model_dump() for s in ranking_item.top_strengths]), hide_index=True, use_container_width=True)

    st.subheader("Risk flags")
    st.write(ranking_item.risk_flags or ["暂无明显风险"])

    st.subheader("成果事件")
    st.dataframe(pd.DataFrame([event.model_dump(mode="json") for event in candidate.achievement_events]), hide_index=True, use_container_width=True)

    st.subheader("职业时间线")
    st.plotly_chart(career_timeline(candidate), use_container_width=True)

    st.subheader("原文证据卡片")
    render_evidence_cards(candidate)
