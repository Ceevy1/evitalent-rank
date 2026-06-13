from __future__ import annotations

import plotly.graph_objects as go


def fairness_shift_chart(fairness: dict):
    shifts = fairness.get("candidate_score_shift", {})
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(shifts), y=list(shifts.values()), marker_color="#4c78a8"))
    fig.update_layout(xaxis_title="候选人编号", yaxis_title="最大 RankScore 变化", height=320)
    return fig
