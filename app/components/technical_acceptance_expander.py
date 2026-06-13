from __future__ import annotations

import streamlit as st


def render_technical_acceptance_expander(summary: dict | None = None) -> None:
    summary = summary or {}
    with st.expander("技术验收信息", expanded=False):
        st.write(
            {
                "当前是否使用本地智能分析": summary.get("provider", "本地智能分析服务") == "本地智能分析服务",
                "当前模型连接是否正常": summary.get("model_connected", "未检测"),
                "当前分析是否仅使用脱敏文本": summary.get("redacted_only", True),
                "成果依据核验通过率": summary.get("grounding_pass_rate", "暂无数据"),
                "隐私风险检测数量": summary.get("sensitive_leakage_count", 0),
                "推理总耗时": summary.get("total_inference_seconds", "暂无数据"),
                "是否使用缓存": summary.get("used_cached_response", False),
                "是否使用 Mock": summary.get("used_mock_response", False),
            }
        )
