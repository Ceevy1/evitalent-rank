from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.metric_cards import render_metric_cards
from app.components.task_header import render_task_header
from app.safe_view_models import load_safe_workspace, local_ranking_rows, official_ranking_rows, processing_rows
from app.ui_copy import DOMAIN_LABELS, REPORT_BOUNDARY_NOTICE, label_for_domain
from app.ui_state import current_task, init_session_state
from evitalent.db import CandidateRecord, DocumentRecord, RankingRecord, get_session
from evitalent.settings import PROJECT_ROOT


def _session_task_rows(tasks: dict) -> list[dict]:
    rows = []
    for task in sorted(tasks.values(), key=lambda item: item.get("created_at", ""), reverse=True):
        rows.append(
            {
                "记录类型": "会话任务",
                "记录编号": task.get("task_id", ""),
                "任务名称": task.get("task_name", "未命名分析任务"),
                "评价领域": label_for_domain(task.get("domain")),
                "岗位名称": task.get("job_title", ""),
                "分析重点": task.get("focus", ""),
                "创建时间": task.get("created_at", ""),
                "_task_id": task.get("task_id", ""),
                "_domain": task.get("domain"),
                "_ranking_id": st.session_state.task_ranking_ids.get(task.get("task_id", "")),
                "_source": "session_task",
            }
        )
    return rows


def _ranking_rows_from_database() -> list[dict]:
    session = get_session()
    try:
        records = list(session.query(RankingRecord).order_by(RankingRecord.created_at.desc()).all())
    finally:
        session.close()
    rows = []
    for record in records:
        rows.append(
            {
                "记录类型": "排名结果",
                "记录编号": record.ranking_id,
                "任务名称": f"{label_for_domain(record.domain)} 排名分析",
                "评价领域": label_for_domain(record.domain),
                "岗位名称": "历史分析批次",
                "分析重点": record.method_version,
                "创建时间": record.created_at.isoformat(timespec="seconds") if record.created_at else "",
                "_task_id": "",
                "_domain": record.domain,
                "_ranking_id": record.ranking_id,
                "_source": "ranking_record",
            }
        )
    return rows


def _ranking_rows_from_files(existing_ids: set[str]) -> list[dict]:
    ranking_dir = PROJECT_ROOT / "data" / "outputs" / "rankings"
    if not ranking_dir.exists():
        return []
    rows = []
    for path in sorted(ranking_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        ranking_id = path.stem
        if ranking_id in existing_ids:
            continue
        payload = _read_json_file(path)
        domain = payload.get("domain")
        if not domain:
            continue
        rows.append(
            {
                "记录类型": "本地排名文件",
                "记录编号": ranking_id,
                "任务名称": f"{label_for_domain(domain)} 排名分析",
                "评价领域": label_for_domain(domain),
                "岗位名称": "历史分析批次",
                "分析重点": payload.get("ranking_method_version", ""),
                "创建时间": payload.get("generated_at", datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")),
                "_task_id": "",
                "_domain": domain,
                "_ranking_id": ranking_id,
                "_source": "ranking_file",
            }
        )
    return rows


def _database_processing_rows() -> list[dict]:
    session = get_session()
    try:
        documents = list(session.query(DocumentRecord).order_by(DocumentRecord.created_at.desc()).all())
        candidates = list(session.query(CandidateRecord).order_by(CandidateRecord.created_at.desc()).all())
    finally:
        session.close()

    rows = []
    extracted_by_document = {candidate.document_id: candidate for candidate in candidates}
    for document in documents:
        candidate = extracted_by_document.get(document.document_id)
        status = "已完成结构化抽取" if candidate else ("已完成隐私处理" if document.redacted_path else "已上传")
        rows.append(
            {
                "候选人编号": candidate.candidate_id if candidate else document.document_id,
                "评价领域": "待分析",
                "当前状态": status,
                "已识别有效成果数": "",
                "提示说明": "来自本地持久化数据库，不展示原始文件名或隐私字段。",
                "创建时间": document.created_at.isoformat(timespec="seconds") if document.created_at else "",
                "status_code": "completed_eligible" if candidate else document.parse_status,
            }
        )
    return rows


def _history_rows(tasks: dict) -> list[dict]:
    ranking_rows = _ranking_rows_from_database()
    existing_ids = {row["_ranking_id"] for row in ranking_rows if row.get("_ranking_id")}
    rows = _session_task_rows(tasks) + ranking_rows + _ranking_rows_from_files(existing_ids)
    return sorted(rows, key=lambda row: row.get("创建时间", ""), reverse=True)


def _rankings_by_domain(history_rows: list[dict], workspace: dict) -> dict[str, list[dict]]:
    rankings: dict[str, list[dict]] = {}
    for domain in DOMAIN_LABELS:
        rows: list[dict] = []
        official_rows = official_ranking_rows(workspace, domain)
        if official_rows:
            rows.extend(official_rows)
        for item in history_rows:
            if item.get("_domain") != domain or not item.get("_ranking_id"):
                continue
            for row in local_ranking_rows(domain, ranking_id=item["_ranking_id"]):
                rows.append({"排名记录编号": item["_ranking_id"], **row})
        if rows:
            rankings[domain] = rows
    return rankings


def _selected_ranking_rows(selected: dict, workspace: dict) -> list[dict]:
    domain = selected.get("_domain")
    ranking_id = selected.get("_ranking_id")
    if not domain:
        return []
    if ranking_id:
        return local_ranking_rows(domain, ranking_id=ranking_id)
    return official_ranking_rows(workspace, domain)


def _official_dataset_summary(workspace: dict) -> list[dict]:
    inventory_by_domain = {row.get("domain"): row for row in workspace.get("inventory", [])}
    ranking_domains = workspace.get("rankings", {}).get("domains", {})
    rows = []
    for domain in DOMAIN_LABELS:
        inventory = inventory_by_domain.get(domain, {})
        ranking = ranking_domains.get(domain, {})
        ranking_rows = ranking.get("ranking", [])
        scores = [float(row.get("rank_score", 0)) for row in ranking_rows]
        rows.append(
            {
                "评价领域": label_for_domain(domain),
                "domain": domain,
                "简历数": int(inventory.get("document_count", 0) or 0),
                "可读简历数": int(inventory.get("readable_count", 0) or 0),
                "不可读简历数": int(inventory.get("unreadable_count", 0) or 0),
                "已排名人数": len(ranking_rows),
                "最高综合竞争力指数": max(scores) if scores else 0,
                "平均综合竞争力指数": round(sum(scores) / len(scores), 2) if scores else 0,
            }
        )
    return rows


def _dataset_coverage_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure()
    x = [row["评价领域"] for row in rows]
    fig.add_bar(name="可读简历数", x=x, y=[row["可读简历数"] for row in rows], marker_color="#2563eb")
    fig.add_bar(name="不可读简历数", x=x, y=[row["不可读简历数"] for row in rows], marker_color="#94a3b8")
    fig.add_bar(name="已排名人数", x=x, y=[row["已排名人数"] for row in rows], marker_color="#16a34a")
    fig.update_layout(title="主办方数据集六领域覆盖与排名产出", barmode="group", height=360, yaxis_title="人数/文件数")
    return fig


def _domain_score_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure()
    x = [row["评价领域"] for row in rows]
    fig.add_bar(name="最高综合竞争力指数", x=x, y=[row["最高综合竞争力指数"] for row in rows], marker_color="#1f3a8a")
    fig.add_bar(name="平均综合竞争力指数", x=x, y=[row["平均综合竞争力指数"] for row in rows], marker_color="#f59e0b")
    fig.update_layout(title="六领域排序分数概览", barmode="group", height=360, yaxis_title="RankScore")
    return fig


def _read_json_file(path: Path) -> dict:
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _csv_for_history(record: dict, process_rows: list[dict], ranking_rows: list[dict]) -> str:
    output = StringIO()
    output.write("section,field,value\n")
    for key, value in record.items():
        if not key.startswith("_"):
            output.write(f'record,{key},"{str(value).replace(chr(34), chr(34) + chr(34))}"\n')
    for index, row in enumerate(process_rows, start=1):
        for key, value in row.items():
            if key != "status_code":
                output.write(f'processing_{index},{key},"{str(value).replace(chr(34), chr(34) + chr(34))}"\n')
    for index, row in enumerate(ranking_rows, start=1):
        for key, value in row.items():
            output.write(f'ranking_{index},{key},"{str(value).replace(chr(34), chr(34) + chr(34))}"\n')
    output.write(f'notice,boundary,"{REPORT_BOUNDARY_NOTICE}"\n')
    return output.getvalue()


def _public_columns(rows: list[dict]) -> list[dict]:
    return [{key: value for key, value in row.items() if not key.startswith("_")} for row in rows]


def render() -> None:
    init_session_state()
    task = current_task()
    render_task_header(task)
    st.title("分析历史记录")
    st.caption("记录每次分析任务的任务信息、处理进度、排名结果、风险提示和可追溯的安全匿名数据。")

    tasks = st.session_state.get("tasks", {})
    workspace = load_safe_workspace()
    process_rows = processing_rows(workspace) + _database_processing_rows()
    history_rows = _history_rows(tasks)
    rankings = _rankings_by_domain(history_rows, workspace)
    total_ranked = sum(len(rows) for rows in rankings.values())
    dataset_summary = _official_dataset_summary(workspace)

    render_metric_cards(
        {
            "历史记录数": len(history_rows),
            "处理记录数": len(process_rows),
            "已排名记录数": total_ranked,
            "覆盖评价领域": len(rankings),
        }
    )

    if not history_rows and not process_rows:
        st.info("尚未找到分析历史。请先在“新建分析任务”中创建岗位分析，并完成简历导入、分析和排序。")
        return

    st.markdown("### 主办方数据集六领域分析可视化")
    st.dataframe(pd.DataFrame([{key: value for key, value in row.items() if key != "domain"} for row in dataset_summary]), hide_index=True, use_container_width=True)
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.plotly_chart(_dataset_coverage_chart(dataset_summary), use_container_width=True)
    with chart_cols[1]:
        st.plotly_chart(_domain_score_chart(dataset_summary), use_container_width=True)

    st.markdown("### 历史记录")
    if history_rows:
        st.dataframe(pd.DataFrame(_public_columns(history_rows)), hide_index=True, use_container_width=True)
    else:
        st.info("尚未找到任务或排名历史，但已发现处理过程记录。")

    selected_record = history_rows[0] if history_rows else {"记录编号": "processing_only", "任务名称": "处理过程记录", "_domain": None, "_ranking_id": None}
    if history_rows:
        options = {f"{row['记录类型']}｜{row['任务名称']}｜{row['记录编号']}": index for index, row in enumerate(history_rows)}
        selected_label = st.selectbox("查看历史详情", list(options.keys()))
        selected_record = history_rows[options[selected_label]]
    selected_rankings = _selected_ranking_rows(selected_record, workspace)

    st.markdown("### 任务详细数据")
    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.write(
            {
                "记录类型": selected_record.get("记录类型"),
                "记录编号": selected_record.get("记录编号"),
                "任务名称": selected_record.get("任务名称"),
                "岗位名称": selected_record.get("岗位名称"),
                "评价领域": selected_record.get("评价领域"),
            }
        )
    with detail_cols[1]:
        st.write(
            {
                "分析重点": selected_record.get("分析重点") or "未填写",
                "处理记录数": len(process_rows),
                "当前记录排名人数": len(selected_rankings),
                "历史记录生成时间": datetime.now().isoformat(timespec="seconds"),
            }
        )

    st.markdown("### 分析过程明细")
    if process_rows:
        st.dataframe(pd.DataFrame(_public_columns(process_rows)), hide_index=True, use_container_width=True)
    else:
        st.info("当前还没有可展示的处理过程记录。")

    st.markdown("### 排名结果明细")
    if selected_rankings:
        st.dataframe(pd.DataFrame(selected_rankings), hide_index=True, use_container_width=True)
    else:
        st.info("当前记录还没有可展示的排名结果。")

    with st.expander("按领域查看全部安全排名记录", expanded=False):
        if not rankings:
            st.info("当前还没有可展示的排名结果。")
        for domain, rows in rankings.items():
            st.markdown(f"#### {label_for_domain(domain)}")
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.download_button(
        "下载当前历史记录 CSV",
        data=_csv_for_history(selected_record, process_rows, selected_rankings).encode("utf-8-sig"),
        file_name=f"analysis_history_{selected_record.get('记录编号', 'history')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.info(REPORT_BOUNDARY_NOTICE)
