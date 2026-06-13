from __future__ import annotations

import pandas as pd
import streamlit as st


def render_evidence_table(rows: list[dict]) -> None:
    if not rows:
        st.info("当前安全摘要中没有可展示的成果证据明细。")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
