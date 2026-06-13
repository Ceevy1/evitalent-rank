from __future__ import annotations

import pandas as pd
import streamlit as st


def render_processing_table(rows: list[dict]) -> None:
    if not rows:
        st.info("当前还没有分析进度。请先完成隐私确认并开始智能分析。")
        return
    safe = [{key: value for key, value in row.items() if key != "status_code"} for row in rows]
    st.dataframe(pd.DataFrame(safe), hide_index=True, use_container_width=True)
