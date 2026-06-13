from __future__ import annotations

import streamlit as st

from app.components.extraction_panel import render_extraction_panel
from evitalent.services.document_service import DocumentService, UnsupportedDocumentType


def render_upload_panel() -> None:
    st.title("简历上传与脱敏预览")
    st.caption("真实上传文件必须先解析与脱敏；结构化抽取只读取脱敏文本。")
    if "last_redacted_document_id" not in st.session_state:
        st.session_state.last_redacted_document_id = None
    files = st.file_uploader("上传 DOCX/PDF", type=["docx", "pdf"], accept_multiple_files=True)
    if st.button("解析并脱敏", disabled=not files):
        service = DocumentService()
        for file in files or []:
            try:
                saved = service.save_upload_bytes(file.name, file.read())
                parsed = service.parse_and_redact(saved["document_id"])
                st.subheader(file.name)
                st.write(f"解析状态：{parsed['parse_status']}")
                st.write(f"命中敏感字段类别：{', '.join(parsed['detected_pii_types']) or '无'}")
                if parsed["warnings"]:
                    st.warning("；".join(parsed["warnings"]))
                st.text_area("脱敏后的文本预览", parsed["redacted_preview"], height=260, key=saved["document_id"])
                st.session_state.last_redacted_document_id = saved["document_id"]
            except UnsupportedDocumentType as exc:
                st.error(str(exc))
            except Exception:
                st.error("解析或脱敏失败，请确认文件为可读取的 DOCX 或文本型 PDF。")
    render_extraction_panel(st.session_state.last_redacted_document_id)
