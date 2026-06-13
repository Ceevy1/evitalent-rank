from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from app.ui_copy import BOUNDARY_NOTICE, DOMAIN_LABELS, REPORT_BOUNDARY_NOTICE, label_for_status
from evitalent.official_samples.manual_review_store import MANUAL_APPROVED, REVIEWABLE_SOURCE_STATUSES
from evitalent.official_samples.risk_issue_review_store import review_key
from evitalent.official_samples.settings import OfficialSampleSettings, load_official_sample_settings
from evitalent.settings import PROJECT_ROOT

FORBIDDEN_VIEW_KEYS = {
    "name",
    "person_name",
    "phone",
    "email",
    "salary",
    "salary_current",
    "salary_expected",
    "marital_status",
    "birth_date",
    "birth_year",
    "original_filename",
    "private_relative_path",
}

RANKING_INCLUDED_STATUSES = {"completed_eligible", MANUAL_APPROVED}


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _risk_issue_review_path(settings: OfficialSampleSettings) -> Path:
    return getattr(settings, "risk_issue_review_path", settings.batch_output_dir / "risk_issue_review_records.json")


def load_safe_workspace(settings: OfficialSampleSettings | None = None) -> dict[str, Any]:
    settings = settings or load_official_sample_settings(create_dirs=False)
    return {
        "inventory": _read_json(settings.inventory_safe_summary_path) or [],
        "redaction_pilot": (_read_json(settings.redaction_pilot_safe_summary_path) or {}).get("documents", []),
        "review_gate": _read_json(settings.review_gate_path),
        "llm_pilot": (_read_json(settings.llm_pilot_safe_summary_path) or {}).get("documents", []),
        "batch": _read_json(settings.batch_output_dir / "safe_processing_summary.json") or [],
        "batch_state": _read_json(settings.batch_state_path) or {"documents": {}},
        "manual_review": _read_json(settings.manual_review_path) or {"reviews": {}},
        "risk_issue_review": _read_json(_risk_issue_review_path(settings)) or {"issue_reviews": {}},
        "rankings": _read_json(settings.rankings_dir / "all_domains_safe_summary.json") or {"domains": {}},
    }


def overview_metrics(workspace: dict[str, Any]) -> dict[str, int]:
    ranked = [
        item
        for domain_payload in workspace.get("rankings", {}).get("domains", {}).values()
        for item in domain_payload.get("ranking", [])
    ]
    batch = workspace.get("batch", [])
    manual_approved = sum(1 for item in workspace.get("manual_review", {}).get("reviews", {}).values() if item.get("manual_status") == MANUAL_APPROVED)
    return {
        "已分析简历数": sum(int(row.get("processed_documents", 0)) for row in batch) or len(ranked),
        "可纳入比较人数": (sum(int(row.get("eligible_documents", 0)) for row in batch) or len(ranked)) + manual_approved,
        "待人工核验人数": sum(int(row.get("needs_review_documents", 0)) for row in batch),
        "人工核验通过": manual_approved,
        "已生成报告数": 1 if ranked else 0,
    }


def processing_rows(workspace: dict[str, Any]) -> list[dict]:
    rows: list[dict] = []
    for row in workspace.get("llm_pilot", []):
        status = "completed_eligible" if row.get("eligible_for_scoring") else "completed_needs_review"
        if row.get("safety_passed") is False:
            status = "failed_safety"
        rows.append(
            {
                "候选人编号": row.get("document_id"),
                "评价领域": DOMAIN_LABELS.get(row.get("folder_domain"), row.get("folder_domain")),
                "当前状态": label_for_status(status),
                "已识别有效成果数": row.get("grounded_event_count", 0),
                "提示说明": "可进入正式比较" if status == "completed_eligible" else "建议人工核验后再使用",
                "status_code": status,
            }
        )
    return rows


def manual_review_rows(workspace: dict[str, Any], session_rows: list[dict] | None = None) -> list[dict]:
    reviews = workspace.get("manual_review", {}).get("reviews", {})
    rows: list[dict] = []
    seen: set[str] = set()
    for item in workspace.get("batch_state", {}).get("documents", {}).values():
        status = item.get("status")
        document_id = item.get("document_id")
        if status not in REVIEWABLE_SOURCE_STATUSES or not document_id:
            continue
        review = reviews.get(document_id, {})
        rows.append(
            {
                "候选人编号": document_id,
                "评价领域": DOMAIN_LABELS.get(item.get("domain"), item.get("domain")),
                "系统状态": label_for_status(status),
                "人工核验状态": label_for_status(review.get("manual_status")) if review else "待处理",
                "审核备注": review.get("note", ""),
                "review_status": review.get("manual_status"),
                "source_status": status,
                "domain": item.get("domain", ""),
            }
        )
        seen.add(document_id)
    for item in session_rows or []:
        status = item.get("status_code")
        document_id = item.get("候选人编号")
        if status not in REVIEWABLE_SOURCE_STATUSES or not document_id or document_id in seen:
            continue
        review = reviews.get(document_id, {})
        rows.append(
            {
                "候选人编号": document_id,
                "评价领域": item.get("评价领域"),
                "系统状态": item.get("当前状态", label_for_status(status)),
                "人工核验状态": label_for_status(review.get("manual_status")) if review else "待处理",
                "审核备注": review.get("note", ""),
                "review_status": review.get("manual_status"),
                "source_status": status,
                "domain": item.get("domain", ""),
            }
        )
    return rows


def official_ranking_rows(workspace: dict[str, Any], domain: str, ranking_id: str | None = None) -> list[dict]:
    payload = workspace.get("rankings", {}).get("domains", {}).get(domain, {})
    rows = []
    for item in payload.get("ranking", []):
        rows.append(
            {
                "排名": item.get("rank"),
                "候选人编号": item.get("document_id"),
                "综合竞争力指数": item.get("rank_score"),
                "能力表现分": item.get("bcs"),
                "材料可信度": item.get("eci"),
                "风险扣减": item.get("penalty"),
                "核心优势": "、".join(item.get("top_strength_labels", [])),
                "待核验事项": "、".join(item.get("risk_flag_types", [])),
                "有依据成果数": item.get("grounded_achievement_count", 0),
            }
        )
    if rows:
        return rows
    if ranking_id:
        return local_ranking_rows(domain, ranking_id=ranking_id)
    return []


def split_risk_issues(text: str | None) -> list[str]:
    if not text:
        return []
    return [item.strip() for item in str(text).split("、") if item.strip()]


def attach_risk_issue_review_status(rows: list[dict], workspace: dict[str, Any]) -> list[dict]:
    reviews = workspace.get("risk_issue_review", {}).get("issue_reviews", {})
    output: list[dict] = []
    for row in rows:
        issues = split_risk_issues(row.get("待核验事项"))
        reviewed_count = sum(1 for issue in issues if reviews.get(review_key(str(row.get("候选人编号")), issue), {}).get("review_status"))
        pending_count = max(len(issues) - reviewed_count, 0)
        next_row = dict(row)
        next_row["待核验处理状态"] = "暂无待核验事项" if not issues else f"已处理 {reviewed_count}/{len(issues)}"
        next_row["待处理事项数"] = pending_count
        next_row["_risk_issue_count"] = len(issues)
        next_row["_pending_risk_issue_count"] = pending_count
        output.append(next_row)
    return output


def risk_issue_review_rows(rows: list[dict], workspace: dict[str, Any], domain: str) -> list[dict]:
    reviews = workspace.get("risk_issue_review", {}).get("issue_reviews", {})
    review_rows: list[dict] = []
    for row in rows:
        document_id = str(row.get("候选人编号", ""))
        for issue in split_risk_issues(row.get("待核验事项")):
            review = reviews.get(review_key(document_id, issue), {})
            review_rows.append(
                {
                    "候选人编号": document_id,
                    "评价领域": DOMAIN_LABELS.get(domain, domain),
                    "待核验事项": issue,
                    "处理状态": label_for_status(review.get("review_status")) if review else "待处理",
                    "处理备注": review.get("note", ""),
                    "review_status": review.get("review_status"),
                    "domain": domain,
                }
            )
    return review_rows


def local_ranking_rows(domain: str, ranking_id: str | None = None) -> list[dict]:
    ranking_dir = PROJECT_ROOT / "data" / "outputs" / "rankings"
    if not ranking_dir.exists():
        return []
    ranking_paths = [ranking_dir / f"{ranking_id}.json"] if ranking_id else sorted(ranking_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in ranking_paths:
        if not path.exists():
            continue
        payload = _read_json(path) or {}
        if payload.get("domain") != domain:
            continue
        rows = []
        for item in payload.get("candidates", []):
            top_strengths = item.get("top_strengths", [])
            labels = [strength.get("label", "") for strength in top_strengths if isinstance(strength, dict)]
            evidence_summary = item.get("evidence_summary", {}) or {}
            rows.append(
                {
                    "排名": item.get("rank"),
                    "候选人编号": item.get("candidate_id") or item.get("display_id"),
                    "综合竞争力指数": item.get("rank_score"),
                    "能力表现分": item.get("bcs"),
                    "材料可信度": item.get("eci"),
                    "风险扣减": item.get("penalty"),
                    "核心优势": "、".join(labels),
                    "待核验事项": "、".join(item.get("risk_flags", [])),
                    "有依据成果数": evidence_summary.get("achievement_event_count", 0),
                }
            )
        return rows
    return []


def filter_formal_ranking(items: list[dict]) -> list[dict]:
    return [item for item in items if item.get("status") in RANKING_INCLUDED_STATUSES or item.get("status_code") in RANKING_INCLUDED_STATUSES]


def has_forbidden_view_keys(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in FORBIDDEN_VIEW_KEYS:
                return True
            if has_forbidden_view_keys(value):
                return True
    elif isinstance(payload, list):
        return any(has_forbidden_view_keys(item) for item in payload)
    return False


def build_csv_ranking_summary(rows: list[dict], task: dict | None = None) -> str:
    output = StringIO()
    fieldnames = [
        "任务名称",
        "评价领域",
        "岗位名称",
        "分析日期",
        "候选人数",
        "排名",
        "候选人编号",
        "综合竞争力指数",
        "能力表现分",
        "材料可信度",
        "风险扣减",
        "核心优势标签",
        "待核验事项类型",
        "有依据成果数量",
        "系统边界说明",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    task = task or {}
    for row in rows:
        writer.writerow(
            {
                "任务名称": task.get("task_name", "未命名分析任务"),
                "评价领域": DOMAIN_LABELS.get(task.get("domain"), task.get("domain", "")),
                "岗位名称": task.get("job_title", ""),
                "分析日期": datetime.now().date().isoformat(),
                "候选人数": len(rows),
                "排名": row.get("排名"),
                "候选人编号": row.get("候选人编号"),
                "综合竞争力指数": row.get("综合竞争力指数"),
                "能力表现分": row.get("能力表现分"),
                "材料可信度": row.get("材料可信度"),
                "风险扣减": row.get("风险扣减"),
                "核心优势标签": row.get("核心优势", ""),
                "待核验事项类型": row.get("待核验事项", ""),
                "有依据成果数量": row.get("有依据成果数", 0),
                "系统边界说明": REPORT_BOUNDARY_NOTICE,
            }
        )
    return output.getvalue()


def build_html_ranking_summary(rows: list[dict], task: dict | None = None) -> str:
    task = task or {}
    body_rows = "\n".join(
        "<tr>"
        f"<td>{row.get('排名', '')}</td><td>{row.get('候选人编号', '')}</td>"
        f"<td>{row.get('综合竞争力指数', '')}</td><td>{row.get('能力表现分', '')}</td>"
        f"<td>{row.get('材料可信度', '')}</td><td>{row.get('风险扣减', '')}</td>"
        f"<td>{row.get('核心优势', '')}</td><td>{row.get('待核验事项', '')}</td>"
        "</tr>"
        for row in rows
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>人才简历综合优选分析报告</title></head>
<body>
<h1>人才简历综合优选分析报告</h1>
<p>任务名称：{task.get('task_name', '未命名分析任务')}</p>
<p>评价领域：{DOMAIN_LABELS.get(task.get('domain'), task.get('domain', ''))}</p>
<p>岗位名称：{task.get('job_title', '')}</p>
<table border="1"><tr><th>排名</th><th>候选人编号</th><th>综合竞争力指数</th><th>能力表现分</th><th>材料可信度</th><th>风险扣减</th><th>核心优势</th><th>待核验事项</th></tr>{body_rows}</table>
<p>{REPORT_BOUNDARY_NOTICE}</p>
</body></html>"""
