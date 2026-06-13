from __future__ import annotations

from datetime import date, datetime

import plotly.graph_objects as go


def _parse_date(value: str | None) -> date:
    if not value:
        return date(2026, 5, 1)
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y.%m", "%Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.date().replace(day=1)
        except ValueError:
            continue
    return date(2026, 5, 1)


def radar_chart(axis_scores: dict[str, float], candidate_id: str):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=list(axis_scores.values()), theta=list(axis_scores.keys()), fill="toself", name=candidate_id))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False, height=420, margin=dict(l=40, r=40, t=40, b=40))
    return fig


def rankscore_bar(rows: list[dict]):
    if not rows:
        return go.Figure()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[row["candidate_id"] for row in rows],
                y=[row["rank_score"] for row in rows],
                text=[f"#{row['rank']}" for row in rows],
                marker=dict(color=[row["eci"] for row in rows], colorscale="Blues", colorbar=dict(title="ECI")),
            )
        ]
    )
    fig.update_layout(xaxis_title="候选人编号", yaxis_title="RankScore", height=360, margin=dict(l=40, r=40, t=30, b=40))
    return fig


def bcs_eci_chart(rows: list[dict]):
    if not rows:
        return go.Figure()
    fig = go.Figure()
    for row in rows:
        fig.add_trace(
            go.Scatter(
                x=[row["bcs"]],
                y=[row["eci"]],
                mode="markers+text",
                text=[row["candidate_id"]],
                textposition="top center",
                marker=dict(size=max(10, row["rank_score"] / 4)),
                name=row["candidate_id"],
            )
        )
    fig.update_layout(xaxis_title="BCS", yaxis_title="ECI", height=380, margin=dict(l=40, r=40, t=30, b=40))
    return fig


def career_timeline(candidate):
    rows = []
    for record in candidate.career_records:
        start = _parse_date(record.start_date)
        end = _parse_date(record.end_date)
        rows.append({"title": record.title, "start": start, "end": end, "days": max((end - start).days, 30)})
    if not rows:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[row["days"] for row in rows],
            y=[row["title"] for row in rows],
            base=[row["start"].isoformat() for row in rows],
            orientation="h",
            marker_color="#2f6f8f",
            text=[f"{row['start'].strftime('%Y-%m')} 至 {row['end'].strftime('%Y-%m')}" for row in rows],
            hovertemplate="%{y}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="时间",
        yaxis_title="岗位",
        height=max(280, 80 * len(rows)),
        margin=dict(l=40, r=40, t=30, b=40),
        showlegend=False,
    )
    fig.update_xaxes(type="date")
    return fig
