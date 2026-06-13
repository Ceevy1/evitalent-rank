from __future__ import annotations

import pandas as pd
import streamlit as st


def ranking_rows(result) -> list[dict]:
    rows = []
    for item in result.candidates:
        rows.append(
            {
                "rank": item.rank,
                "candidate_id": item.candidate_id,
                "bcs": item.bcs,
                "eci": item.eci,
                "penalty": item.penalty,
                "rank_score": item.rank_score,
                "top_strengths": "；".join(strength.label for strength in item.top_strengths),
                "risk_flags": "；".join(item.risk_flags[:3]),
            }
        )
    return rows


def render_ranking_table(result) -> None:
    st.dataframe(pd.DataFrame(ranking_rows(result)), hide_index=True, use_container_width=True)
