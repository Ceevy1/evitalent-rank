from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.comparison_charts import status_distribution_chart
from app.components.manual_review_panel import render_manual_review_panel
from app.components.metric_cards import render_metric_cards
from app.page_navigation import switch_to_page
from app.components.processing_table import render_processing_table
from app.components.task_header import render_task_header
from app.safe_view_models import load_safe_workspace, manual_review_rows, processing_rows
from app.ui_state import current_task, init_session_state
from evitalent.db import get_session
from evitalent.repositories import CandidateRepository, DocumentRepository, RankingRepository
from evitalent.services.extraction_service import ExtractionService, ExtractionServiceError
from evitalent.services.ranking_service import RankingService


def _session_processing_rows(task_id: str | None) -> list[dict]:
    if not task_id:
        return []
    return st.session_state.analysis_processing_rows_by_task.get(task_id, [])


def _run_uploaded_document_analysis(task: dict) -> None:
    task_id = task["task_id"]
    domain = task["domain"]
    document_ids = st.session_state.uploaded_document_ids_by_task.get(task_id, [])
    if not document_ids:
        st.warning("尚未找到本次上传并完成隐私处理的简历，请先进入“简历导入与隐私检查”完成导入。")
        return

    session = get_session()
    extracted_ids_by_task = st.session_state.extracted_candidate_ids_by_task
    extracted_ids = dict(extracted_ids_by_task.get(task_id, {}))
    rows_by_task = st.session_state.analysis_processing_rows_by_task
    rows = list(rows_by_task.get(task_id, []))
    total_steps = max(len(document_ids), 1) + 1
    completed_steps = 0
    status_box = st.status("正在准备智能分析任务...", expanded=True)
    progress_bar = st.progress(0, text="准备调用本地智能分析服务")

    def update_progress(message: str, *, state: str = "running") -> None:
        progress = min(completed_steps / total_steps, 1.0)
        progress_bar.progress(progress, text=message)
        status_box.update(label=message, state=state, expanded=True)
        status_box.write(message)

    try:
        extraction = ExtractionService(
            document_repository=DocumentRepository(session),
            candidate_repository=CandidateRepository(session),
        )
        update_progress(f"已进入智能分析阶段，本次将处理 {len(document_ids)} 份当前岗位方向简历。")
        for document_id in document_ids:
            if document_id in extracted_ids:
                completed_steps += 1
                update_progress(f"候选人 {extracted_ids[document_id]} 已完成抽取，跳过重复分析。")
                continue
            try:
                update_progress(f"正在调用 Ollama 抽取匿名简历 {document_id} 的结构化信息...")
                summary = extraction.extract_document(document_id, "local_ollama")
                candidate_id = summary["candidate_id"]
                extracted_ids[document_id] = candidate_id
                status = "可纳入比较" if summary.get("eligible_for_scoring") else "待人工核验"
                rows.append(
                    {
                        "候选人编号": candidate_id,
                        "评价领域": domain,
                        "当前状态": status,
                        "已识别有效成果数": summary.get("grounded_event_count", summary.get("achievement_count", 0)),
                        "提示说明": "已完成结构化抽取，可生成排序。" if summary.get("eligible_for_scoring") else "存在待核验事项，建议人工确认。",
                        "status_code": "completed_eligible" if summary.get("eligible_for_scoring") else "completed_needs_review",
                    }
                )
                completed_steps += 1
                update_progress(f"候选人 {candidate_id} 分析完成，已识别 {summary.get('grounded_event_count', summary.get('achievement_count', 0))} 条有效成果。")
            except ExtractionServiceError as exc:
                rows.append(
                    {
                        "候选人编号": document_id,
                        "评价领域": domain,
                        "当前状态": "智能分析暂未完成",
                        "已识别有效成果数": 0,
                        "提示说明": str(exc),
                        "status_code": "failed_model_request",
                    }
                )
                completed_steps += 1
                update_progress(f"匿名简历 {document_id} 分析暂未完成，已记录失败原因并继续处理后续简历。")

        candidate_ids = list(extracted_ids.values())
        if not candidate_ids:
            rows_by_task[task_id] = rows
            st.session_state.analysis_processing_rows_by_task = rows_by_task
            status_box.update(label="智能分析未生成可排序候选人", state="error", expanded=True)
            progress_bar.progress(1.0, text="未生成可排序候选人")
            st.error("尚未生成可用于排序的候选人结构化结果。")
            return

        update_progress("结构化分析完成，正在生成当前岗位方向的排序结果...")
        ranking = RankingService(
            RankingRepository(session),
            candidate_repository=CandidateRepository(session),
        ).create_ranking(domain, candidate_ids, mode="extracted")
        completed_steps = total_steps
        progress_bar.progress(1.0, text="智能分析与排序已完成")
        status_box.update(label="智能分析与排序已完成，即将进入人才排名与对比。", state="complete", expanded=True)
        status_box.write(f"已生成排序记录：{ranking.ranking_id}")
        extracted_ids_by_task[task_id] = extracted_ids
        rows_by_task[task_id] = rows
        st.session_state.extracted_candidate_ids_by_task = extracted_ids_by_task
        st.session_state.analysis_processing_rows_by_task = rows_by_task
        st.session_state.extracted_candidate_ids_by_document = extracted_ids
        st.session_state.analysis_processing_rows = rows
        st.session_state.task_ranking_ids[task_id] = ranking.ranking_id
        st.session_state.selected_ranking_id = ranking.ranking_id
        st.success("智能分析与排序已完成，请进入“人才排名与对比”查看结果。")
        switch_to_page("ranking")
    except Exception as exc:
        status_box.update(label="智能分析流程异常中断", state="error", expanded=True)
        progress_bar.progress(1.0, text="智能分析流程异常中断")
        st.error(f"生成排序失败：{type(exc).__name__}")
    finally:
        session.close()


def render() -> None:
    init_session_state()
    task = current_task()
    render_task_header(task)
    st.title("分析进度")
    if not task:
        st.warning("请先新建分析任务。每个任务只分析同一岗位方向下的简历。")
        return
    workspace = load_safe_workspace()
    rows = processing_rows(workspace) + _session_processing_rows(task["task_id"])
    render_metric_cards(
        {
            "已导入": len(workspace.get("redaction_pilot", [])) + len(st.session_state.redacted_document_rows_by_task.get(task["task_id"], [])),
            "正在分析": sum(1 for row in rows if row.get("当前状态") == "正在智能分析"),
            "可纳入比较": sum(1 for row in rows if row.get("当前状态") == "可纳入比较"),
            "待人工核验": sum(1 for row in rows if "核验" in row.get("当前状态", "")),
        }
    )
    render_processing_table(rows)
    render_manual_review_panel(manual_review_rows(workspace, _session_processing_rows(task["task_id"])))
    st.plotly_chart(status_distribution_chart(rows), use_container_width=True)
    uploaded_rows = st.session_state.redacted_document_rows_by_task.get(task["task_id"], [])
    if uploaded_rows:
        st.markdown("### 本次上传待分析简历")
        st.dataframe(pd.DataFrame(uploaded_rows), hide_index=True, use_container_width=True)
    disabled = not st.session_state.uploaded_document_ids_by_task.get(task["task_id"])
    if st.button("开始智能分析并生成排序", disabled=disabled):
        st.toast("已开始智能分析，请在进度反馈栏查看处理状态。")
        _run_uploaded_document_analysis(task)
