from __future__ import annotations

import pandas as pd
import streamlit as st

from evitalent.interview.models import InterviewScorecardDimension


def render_interview_scorecard_panel(dimensions: list[InterviewScorecardDimension]) -> None:
    rows = [
        {
            "维度": item.dimension,
            "建议权重": item.weight,
            "观察点": "；".join(item.observation_points),
        }
        for item in dimensions
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
