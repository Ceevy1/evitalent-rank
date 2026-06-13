from __future__ import annotations

import pandas as pd
import streamlit as st

from app.ui_copy import label_for_status
from evitalent.official_samples.manual_review_store import (
    MANUAL_APPROVED,
    MANUAL_NEEDS_FOLLOW_UP,
    MANUAL_REJECTED,
    ManualReviewStore,
)
from evitalent.official_samples.settings import load_official_sample_settings


DECISION_LABELS = {
    "通过并纳入后续比较": MANUAL_APPROVED,
    "驳回，不纳入比较": MANUAL_REJECTED,
    "需补充材料后再核验": MANUAL_NEEDS_FOLLOW_UP,
}


def render_manual_review_panel(rows: list[dict]) -> None:
    st.markdown("### 人工核验")
    st.caption("仅展示匿名候选人编号、领域和系统状态。人工结论用于补充模型未能自动通过的样本核验。")
    if not rows:
        st.info("当前没有待人工核验的简历样本。")
        return

    visible_rows = [
        {key: value for key, value in row.items() if key not in {"review_status", "source_status", "domain"}}
        for row in rows
    ]
    st.dataframe(pd.DataFrame(visible_rows), hide_index=True, use_container_width=True)

    selected = st.selectbox(
        "选择核验样本",
        rows,
        format_func=lambda row: f"{row.get('候选人编号')} · {row.get('评价领域')} · {row.get('系统状态')}",
    )
    decision_label = st.radio("核验结论", list(DECISION_LABELS), horizontal=True)
    reviewer = st.text_input("审核人", value="人工审核员")
    note = st.text_area("核验备注", placeholder="记录通过依据、驳回原因或需补充的信息。")
    if st.button("保存核验结论", type="primary", disabled=not selected):
        settings = load_official_sample_settings(create_dirs=True)
        store = ManualReviewStore(settings.manual_review_path)
        store.record(
            str(selected["候选人编号"]),
            domain=str(selected.get("domain") or selected.get("评价领域") or ""),
            source_status=str(selected["source_status"]),
            decision=DECISION_LABELS[decision_label],
            reviewer=reviewer,
            note=note,
        )
        st.success(f"{selected['候选人编号']} 已标记为：{label_for_status(DECISION_LABELS[decision_label])}")
        st.rerun()
