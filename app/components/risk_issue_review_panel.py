from __future__ import annotations

import pandas as pd
import streamlit as st

from app.ui_copy import label_for_status
from evitalent.official_samples.risk_issue_review_store import (
    ISSUE_CONFIRMED_RESOLVED,
    ISSUE_NEEDS_MATERIAL,
    ISSUE_RISK_RETAINED,
    RiskIssueReviewStore,
)
from evitalent.official_samples.settings import load_official_sample_settings


DECISION_LABELS = {
    "已核验通过": ISSUE_CONFIRMED_RESOLVED,
    "维持风险提示": ISSUE_RISK_RETAINED,
    "需补充材料": ISSUE_NEEDS_MATERIAL,
}


def render_risk_issue_review_panel(rows: list[dict]) -> None:
    st.markdown("### 待核验事项处理")
    st.caption("仅记录匿名候选人编号、事项类型、处理结论和备注；不会修改评分权重、RankScore 或原始简历。")
    if not rows:
        st.info("当前筛选范围内没有待核验事项。")
        return

    visible_rows = [{key: value for key, value in row.items() if key not in {"review_status", "domain"}} for row in rows]
    st.dataframe(pd.DataFrame(visible_rows), hide_index=True, use_container_width=True)

    selected = st.selectbox(
        "选择待处理事项",
        rows,
        format_func=lambda row: f"{row.get('候选人编号')} · {row.get('待核验事项')}",
    )
    decision_label = st.radio("处理结论", list(DECISION_LABELS), horizontal=True)
    reviewer = st.text_input("处理人", value="人工审核员", key="risk_issue_reviewer")
    note = st.text_area("处理备注", placeholder="记录核验依据、保留风险原因或需补充的材料。", key="risk_issue_note")
    if st.button("保存事项处理结果", type="primary", disabled=not selected):
        settings = load_official_sample_settings(create_dirs=True)
        store = RiskIssueReviewStore(settings.risk_issue_review_path)
        store.record(
            str(selected["候选人编号"]),
            domain=str(selected.get("domain") or ""),
            issue=str(selected["待核验事项"]),
            decision=DECISION_LABELS[decision_label],
            reviewer=reviewer,
            note=note,
        )
        st.success(f"已保存：{selected['候选人编号']} · {label_for_status(DECISION_LABELS[decision_label])}")
        st.rerun()
