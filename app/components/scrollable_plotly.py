from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit.components.v1 as components


DEFAULT_VIEWPORT_WIDTH = 980
DEFAULT_MIN_CHART_WIDTH = 880
DEFAULT_BAR_WIDTH = 150


def render_scrollable_plotly_chart(
    fig: go.Figure,
    *,
    item_count: int = 0,
    height: int = 380,
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
    min_chart_width: int = DEFAULT_MIN_CHART_WIDTH,
    per_item_width: int = DEFAULT_BAR_WIDTH,
) -> None:
    chart_width = max(min_chart_width, max(item_count, 1) * per_item_width)
    fig.update_layout(width=chart_width, height=height, autosize=False)
    html = pio.to_html(
        fig,
        include_plotlyjs=True,
        full_html=False,
        config={"displayModeBar": False, "responsive": False},
        default_width=f"{chart_width}px",
        default_height=f"{height}px",
    )
    components.html(
        f"""
        <div style="width:min({viewport_width}px, 100%); overflow-x:auto; overflow-y:hidden;">
          <div style="width:{chart_width}px;">
            {html}
          </div>
        </div>
        """,
        height=height + 36,
        scrolling=False,
    )
