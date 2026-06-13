from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from evitalent.models.audit import AuditResult, OverallConclusion


DEFAULT_LIMITATIONS = [
    "本系统为简历材料基础上的辅助排序工具，不替代面试、背景调查和最终录用判断。",
    "简历中未披露的信息不能被系统视为候选人不具备相应能力。",
    "LLM 抽取结果仍需要人工抽检。",
    "当前销售与研发领域规则仍需要更多样本和专家标注校准。",
]


def build_audit_result(
    ranking_id: str,
    domain: str,
    timeline_audit: dict | None = None,
    fairness_audit: dict | None = None,
    robustness_audit: dict | None = None,
    audit_id: str | None = None,
) -> AuditResult:
    timeline = timeline_audit or {}
    fairness = fairness_audit or {}
    robustness = robustness_audit or {}
    critical = int(timeline.get("critical_issue_count", 0))
    critical += len([issue for issue in fairness.get("detected_issues", []) if issue.get("severity") == "critical"])

    status = "passed"
    if fairness.get("fairness_audit_status") == "failed" or critical > 0:
        status = "failed"
    elif timeline.get("issue_count", 0) or robustness.get("robustness_audit_status") == "warning":
        status = "warning"

    summary = []
    if fairness:
        if fairness.get("max_rank_shift", 0) == 0 and fairness.get("max_score_shift", 0) == 0:
            summary.append("本次排序使用脱敏数据生成，确定性评分过程未发现敏感属性影响。")
        else:
            summary.append("敏感字段反事实测试出现分数或排名变化，应先修复配置泄露问题。")
    if robustness:
        full_cmp = robustness.get("comparisons", {}).get("fact_only_text", {})
        consistency = full_cmp.get("top_k_consistency")
        if consistency is not None:
            summary.append(f"候选人排名在事实压缩表达下保持稳定，Top-K 一致率为 {consistency:.0%}。")
    if timeline.get("issue_count", 0):
        summary.append("存在工作经历时间线风险，建议人工核验后再用于决策。")
    if not summary:
        summary.append("未发现关键审计风险。")

    return AuditResult(
        audit_id=audit_id or f"audit_{uuid4().hex[:10]}",
        ranking_id=ranking_id,
        domain=domain,
        generated_at=datetime.now(timezone.utc).isoformat(),
        timeline_audit=timeline,
        fairness_audit=fairness,
        robustness_audit=robustness,
        overall_conclusion=OverallConclusion(
            overall_audit_status=status,
            conclusion_summary=summary,
            critical_issue_count=critical,
        ),
        limitations=DEFAULT_LIMITATIONS,
    )
