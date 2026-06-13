from __future__ import annotations

import plotly.graph_objects as go


def robustness_rank_shift_chart(robustness: dict):
    comparisons = robustness.get("comparisons", {})
    names = list(comparisons)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=[comparisons[name].get("mean_rank_shift", 0) for name in names], name="Mean rank shift"))
    fig.add_trace(go.Bar(x=names, y=[comparisons[name].get("max_rank_shift", 0) for name in names], name="Max rank shift"))
    fig.update_layout(barmode="group", xaxis_title="文本版本", yaxis_title="排名变化", height=340)
    return fig
