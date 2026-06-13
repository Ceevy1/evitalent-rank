from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.redaction_review_panel import render_redaction_review_panel
from app.page_navigation import switch_to_page
from app.components.task_header import render_task_header
from app.safe_view_models import load_safe_workspace
from app.ui_state import current_task, init_session_state, official_review_confirmed
from evitalent.db import get_session
from evitalent.repositories import DocumentRepository
from evitalent.services.document_service import DocumentService, UnsupportedDocumentType


def render() -> None:
    init_session_state()
    task = current_task()
    render_task_header(task)
    st.title("简历导入与隐私检查")
    if not task:
        st.warning("请先新建分析任务，并明确岗位名称与评价领域后，再导入该岗位方向下的候选人简历。")
        return
    task_id = task["task_id"]
    st.write("请上传同一岗位方向下的候选人简历，系统将先进行隐私保护处理。")
    st.info(f"当前任务岗位：{task.get('job_title', '')}；评价领域：{task.get('domain', '')}。本批次只应导入该岗位方向的简历。")
    uploaded = st.file_uploader("上传 DOCX 简历", type=["docx"], accept_multiple_files=True, key=f"resume_upload_{task_id}")
    if uploaded:
        st.info(f"已选择 {len(uploaded)} 份文件。页面不会展示原始文件名，后续将使用匿名编号。")
    if st.button("开始隐私保护处理", disabled=not uploaded):
        session = get_session()
        service = DocumentService(DocumentRepository(session))
        redacted_rows = []
        document_ids = []
        try:
            for file in uploaded or []:
                saved = service.save_upload_bytes(file.name, file.read())
                parsed = service.parse_and_redact(saved["document_id"])
                document_ids.append(saved["document_id"])
                redacted_rows.append(
                    {
                        "候选人编号": saved["document_id"],
                        "隐私处理状态": "已完成",
                        "解析状态": parsed["parse_status"],
                        "命中敏感字段类别数": len(parsed["detected_pii_types"]),
                        "解析提示数": len(parsed["warnings"]),
                    }
                )
            st.session_state.uploaded_document_ids_by_task[task_id] = document_ids
            st.session_state.redacted_document_rows_by_task[task_id] = redacted_rows
            st.session_state.uploaded_document_ids = document_ids
            st.session_state.redacted_document_rows = redacted_rows
            st.success("隐私保护处理已完成，可以进入分析进度页面开始智能分析。")
        except UnsupportedDocumentType as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"隐私保护处理失败：{type(exc).__name__}")
        finally:
            session.close()
    task_redacted_rows = st.session_state.redacted_document_rows_by_task.get(task_id, [])
    if task_redacted_rows:
        st.markdown("### 本次上传隐私处理结果")
        st.dataframe(pd.DataFrame(task_redacted_rows), hide_index=True, use_container_width=True)

    workspace = load_safe_workspace()
    st.markdown("### 主办方样本脱敏 pilot 状态")
    render_redaction_review_panel(workspace.get("redaction_pilot", []))
    confirmed = official_review_confirmed(workspace.get("review_gate")) or bool(task_redacted_rows)
    if confirmed:
        st.success("已完成人工确认，可以进入分析流程。")
    else:
        st.warning("请先查看并确认隐私保护处理结果，再开始智能分析。")
    if st.button("进入分析进度", disabled=not confirmed):
        switch_to_page("processing_status")
