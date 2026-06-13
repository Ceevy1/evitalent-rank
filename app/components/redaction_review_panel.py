from __future__ import annotations

import pandas as pd
import streamlit as st


def render_redaction_review_panel(rows: list[dict]) -> None:
    if not rows:
        st.info("当前任务尚未导入简历，请上传 DOCX 文件开始分析。")
        return
    view_rows = []
    for index, row in enumerate(rows, start=1):
        view_rows.append(
            {
                "候选人编号": row.get("document_id", f"上传文件 {index:02d}"),
                "文件读取状态": row.get("parse_status", "等待处理"),
                "隐私保护状态": row.get("redaction_status", "等待处理"),
                "命中隐私信息类型数量": len(row.get("detected_pii_type_counts", {})),
                "安全检查状态": "通过" if row.get("safety_passed") else "待核验",
            }
        )
    st.dataframe(pd.DataFrame(view_rows), hide_index=True, use_container_width=True)
    st.caption("仅展示匿名编号和隐私类型数量，不展示原始文件名或敏感字段值。")
