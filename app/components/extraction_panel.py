from __future__ import annotations

import streamlit as st

from evitalent.services.extraction_service import ExtractionService, ExtractionServiceError
from evitalent.extraction.llm_client import LLMClient
from evitalent.settings import get_settings


def render_extraction_panel(document_id: str | None) -> None:
    st.subheader("结构化抽取")
    st.info("系统默认仅向模型提交脱敏后的文本。远程兼容 API 模式需要用户自行确认数据使用政策；本系统仅作辅助分析，不构成最终录用结论。")
    settings = get_settings()
    cols = st.columns(4)
    cols[0].metric("extraction_mode", settings.default_extraction_mode)
    cols[1].metric("provider", settings.llm_provider)
    cols[2].metric("model_name", settings.llm_model or "未配置")
    cols[3].metric("使用 Mock", "是" if settings.llm_provider == "mock" else "否")
    if st.button("检查 Ollama 连接"):
        result = LLMClient(provider="local_ollama", base_url="http://127.0.0.1:11434", api_key="ollama", model="evitalent-extractor:7b", temperature=0, seed=9).health_check()
        st.write(f"Ollama 连接状态：{'可用' if result.ok else '不可用'}")
    mode = st.radio(
        "抽取模式",
        ["mock", "local_ollama", "compatible_api"],
        format_func=lambda value: {"mock": "Mock 示例演示", "local_ollama": "本地 Ollama", "compatible_api": "兼容 API"}[value],
        horizontal=True,
    )
    if mode == "compatible_api":
        st.warning("兼容 API 会调用远程接口，请确认只发送脱敏文本并已理解对方数据政策。")
    disabled = not document_id and mode != "mock"
    if st.button("开始结构化抽取", disabled=disabled):
        try:
            target_id = document_id or "demo_hr_001"
            summary = ExtractionService().extract_document(target_id, mode)
            st.success("结构化抽取校验通过。")
            cols = st.columns(4)
            cols[0].metric("候选人编号", summary["candidate_id"])
            cols[1].metric("成果事件", summary["achievement_count"])
            cols[2].metric("证据条数", summary["evidence_count"])
            cols[3].metric("可评分", "是" if summary["eligible_for_scoring"] else "否")
            st.write(f"识别领域：{', '.join(summary['detected_domains']) or '未识别'}")
            if summary["quality_flags"]:
                st.warning("；".join(summary["quality_flags"]))
            st.write("原文证据由模型辅助提取并经本地校验；标准事件类型由规则引擎映射；评分仅使用已通过证据校验和标准化的成果。")
            rows = summary.get("achievement_validation_rows") or []
            if rows:
                st.dataframe(rows, hide_index=True, use_container_width=True)
            if summary["eligible_for_scoring"]:
                st.button("加入排名分析", disabled=True, help="API 已支持 extracted 模式；页面批量真实排名将在 Stage 7 完善。")
        except ExtractionServiceError as exc:
            st.error(str(exc))
        except Exception:
            st.error("结构化抽取失败，请检查模型配置或改用 Mock 示例演示。")
