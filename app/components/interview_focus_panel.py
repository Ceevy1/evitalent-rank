from __future__ import annotations

import streamlit as st

from app.components.interview_question_card import render_interview_question_card
from app.components.interview_scorecard_panel import render_interview_scorecard_panel
from evitalent.interview.interview_recommendation_service import InterviewRecommendationService


def _analysis_from_safe_row(row: dict, domain: str, job_title: str = "") -> dict:
    risk_flags = [item.strip() for item in str(row.get("待核验事项") or "").split("、") if item.strip()]
    strengths = [{"label": item.strip(), "score": 75} for item in str(row.get("核心优势") or "").split("、") if item.strip()]
    return {
        "candidate_id": row.get("候选人编号"),
        "target_domain": domain,
        "job_title": job_title or "目标岗位",
        "rank_score": row.get("综合竞争力指数", 0),
        "bcs": row.get("能力表现分", 0),
        "eci": row.get("材料可信度", 0),
        "penalty": row.get("风险扣减", 0),
        "axis_scores": {},
        "top_strengths": strengths,
        "risk_flags": risk_flags,
        "normalized_achievement_events": [],
        "grounded_evidence_items": [],
        "career_records": [],
    }


def render_interview_focus_panel(row: dict, domain: str, job_title: str = "") -> None:
    recommendation = InterviewRecommendationService().recommend(_analysis_from_safe_row(row, domain, job_title))
    st.markdown("### 面试重点推荐")
    st.info("以下内容仅用于面试辅助，不构成录用或淘汰决定。")
    st.write(f"候选人编号：{recommendation.candidate_id}")
    st.write(f"目标岗位：{recommendation.job_title}")
    st.write(recommendation.fit_summary)

    st.markdown("#### 最契合岗位的能力条件")
    cols = st.columns(min(3, max(1, len(recommendation.high_fit_conditions))))
    for index, condition in enumerate(recommendation.high_fit_conditions):
        with cols[index % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**{condition.label}**")
                st.caption(f"契合程度：{condition.fit_level} ｜ 置信度：{condition.confidence}")
                st.write(condition.basis)

    st.markdown("#### 建议重点考察方向")
    for focus in recommendation.interview_focus_areas:
        with st.container(border=True):
            st.markdown(f"**{focus.focus_name}**")
            st.caption(f"类型：{focus.focus_type} ｜ 优先级：{focus.priority}")
            st.write(focus.reason)

    st.markdown("#### 推荐面试问题")
    for question in recommendation.recommended_questions:
        render_interview_question_card(question)

    st.markdown("#### 待核验事项")
    if recommendation.risk_verification_items:
        for item in recommendation.risk_verification_items:
            with st.container(border=True):
                st.markdown(f"**{item.risk_type}**")
                st.write(item.description)
                st.write(f"建议追问：{item.suggested_probe}")
    else:
        st.write("暂无明显待核验事项。")

    st.markdown("#### 建议面试评分表")
    render_interview_scorecard_panel(recommendation.suggested_interview_scorecard)
    if recommendation.limitations:
        st.caption("；".join(recommendation.limitations))
