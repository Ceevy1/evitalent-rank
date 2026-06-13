from __future__ import annotations

import plotly.graph_objects as go

from app.ui_copy import AXIS_LABELS


def rankscore_bar_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure()
    if rows:
        fig.add_bar(
            x=[row["候选人编号"] for row in rows],
            y=[row["综合竞争力指数"] for row in rows],
            marker_color="#1f3a8a",
            text=[row["排名"] for row in rows],
        )
    fig.update_layout(title="综合竞争力指数", xaxis_title="候选人编号", yaxis_title="综合竞争力指数", height=360, bargap=0.35)
    return fig


def bcs_eci_grouped_bar(rows: list[dict]) -> go.Figure:
    fig = go.Figure()
    if rows:
        x = [row["候选人编号"] for row in rows]
        fig.add_bar(name="能力表现分", x=x, y=[row["能力表现分"] for row in rows], marker_color="#2563eb")
        fig.add_bar(name="材料可信度", x=x, y=[row["材料可信度"] for row in rows], marker_color="#16a34a")
    fig.update_layout(barmode="group", height=360, yaxis_title="分数", bargap=0.32, bargroupgap=0.08)
    return fig


def radar_compare_chart(items: list[dict]) -> go.Figure:
    fig = go.Figure()
    axes = list(AXIS_LABELS)
    for item in items[:3]:
        scores = item.get("axis_scores") or {axis: 0 for axis in axes}
        fig.add_trace(
            go.Scatterpolar(
                r=[scores.get(axis, 0) for axis in axes],
                theta=[AXIS_LABELS[axis] for axis in axes],
                fill="toself",
                name=item.get("candidate_id") or item.get("候选人编号"),
            )
        )
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=420)
    return fig


def status_distribution_chart(rows: list[dict]) -> go.Figure:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("当前状态", "未知状态")
        counts[status] = counts.get(status, 0) + 1
    fig = go.Figure()
    if counts:
        fig.add_bar(x=list(counts), y=list(counts.values()), marker_color="#64748b")
    fig.update_layout(height=300, xaxis_title="状态", yaxis_title="人数")
    return fig
