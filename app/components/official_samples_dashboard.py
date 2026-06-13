from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.components.manual_review_panel import render_manual_review_panel
from app.safe_view_models import load_safe_workspace, manual_review_rows
from evitalent.official_samples.private_manifest import read_json
from evitalent.official_samples.settings import load_official_sample_settings


def _load(path: Path):
    return read_json(path) if path.exists() else None


def render_official_samples_dashboard() -> None:
    st.header("主办方样本分析")
    st.info("系统默认仅处理脱敏后的简历文本，排名结果用于比赛分析与辅助评价，不构成最终录用结论。")
    settings = load_official_sample_settings(create_dirs=False)

    inventory = _load(settings.inventory_safe_summary_path)
    if inventory:
        st.subheader("文件盘点安全摘要")
        st.dataframe(pd.DataFrame(inventory), use_container_width=True)
    else:
        st.warning("尚未生成文件盘点安全摘要。")

    st.subheader("Pilot 状态")
    redaction = _load(settings.redaction_pilot_safe_summary_path)
    gate = _load(settings.review_gate_path)
    llm_pilot = _load(settings.llm_pilot_safe_summary_path)
    st.write(
        {
            "redaction_pilot_completed": redaction is not None,
            "manual_review_confirmed": bool(gate and gate.get("review_confirmed") is True),
            "local_ollama_pilot_completed": llm_pilot is not None,
        }
    )
    if redaction:
        st.dataframe(pd.DataFrame(redaction.get("documents", redaction)), use_container_width=True)

    st.subheader("Batch 状态")
    batch = _load(settings.batch_output_dir / "safe_processing_summary.json")
    if batch:
        st.dataframe(pd.DataFrame(batch), use_container_width=True)
    else:
        st.caption("尚未运行批量处理。")

    render_manual_review_panel(manual_review_rows(load_safe_workspace(settings)))

    st.subheader("匿名排名")
    rankings = _load(settings.rankings_dir / "all_domains_safe_summary.json")
    if rankings:
        domain = st.selectbox("领域", list(rankings.get("domains", {}).keys()))
        st.dataframe(pd.DataFrame(rankings["domains"][domain].get("ranking", [])), use_container_width=True)
    else:
        st.caption("尚未生成安全排名摘要。")
