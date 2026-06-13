from __future__ import annotations

import streamlit as st


DOMAIN_LABELS = {
    "ecommerce": "电商",
    "brand": "品牌",
    "hr": "人力资源",
    "production": "生产",
    "sales": "销售",
    "rd": "研发",
}


def render_overview() -> None:
    st.title("EviTalent-Rank 人才简历综合优选系统")
    st.write("基于证据约束与确定性评分规则，对六个领域候选人进行竞争力排序和解释。")
    cols = st.columns(6)
    for col, (domain, label) in zip(cols, DOMAIN_LABELS.items()):
        col.metric(label, domain)
    st.subheader("技术流程")
    st.write("文档解析 → 隐私脱敏 → 结构化抽取 → 领域评分 → 排名解释 → 审计分析")
    st.info("V1 为辅助评价系统，不替代最终招聘决策。真实上传简历在 Stage 5 仅支持解析与脱敏预览。")
