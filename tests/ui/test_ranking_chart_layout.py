from __future__ import annotations

from pathlib import Path


def test_ranking_page_uses_fixed_scrollable_chart_container():
    ranking_page = Path("app/pages/ranking_page.py").read_text(encoding="utf-8")
    helper = Path("app/components/scrollable_plotly.py").read_text(encoding="utf-8")
    charts = Path("app/components/comparison_charts.py").read_text(encoding="utf-8")

    assert "render_scrollable_plotly_chart(rankscore_bar_chart(shown)" in ranking_page
    assert "render_scrollable_plotly_chart(bcs_eci_grouped_bar(shown)" in ranking_page
    assert "st.plotly_chart(rankscore_bar_chart(shown), use_container_width=True)" not in ranking_page
    assert "st.plotly_chart(bcs_eci_grouped_bar(shown), use_container_width=True)" not in ranking_page
    assert "overflow-x:auto" in helper
    assert "DEFAULT_VIEWPORT_WIDTH = 980" in helper
    assert "bargap=0.35" in charts
