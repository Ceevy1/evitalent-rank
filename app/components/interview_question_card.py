from __future__ import annotations

import streamlit as st

from evitalent.interview.models import RecommendedQuestion


def render_interview_question_card(question: RecommendedQuestion) -> None:
    with st.container(border=True):
        st.markdown(f"**{question.question}**")
        st.caption(f"考察维度：{question.suggested_score_dimension} ｜ 对应能力：{question.related_competency}")
        st.write(f"为什么问：{question.why_ask}")
        st.write(f"追问建议：{question.follow_up_probe}")
        st.write(f"好回答应包含：{question.expected_good_answer}")
        if question.red_flags:
            st.warning("红旗信号：" + "；".join(question.red_flags))
