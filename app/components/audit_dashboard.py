from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components.fairness_charts import fairness_shift_chart
from app.components.robustness_charts import robustness_rank_shift_chart
from evitalent.audit.audit_report_builder import build_audit_result
from evitalent.audit.fairness_audit import run_fairness_audit
from evitalent.audit.robustness_audit import run_robustness_audit
from evitalent.audit.timeline_audit import run_timeline_audit
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates


def render_audit_dashboard(domain: str) -> None:
    st.title("可信度与公平审计")
    candidates = [c for c in MockExtractor().load_all() if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]
    ranking = rank_candidates(candidates, domain, ranking_id=f"audit_streamlit_{domain}")
    timeline = run_timeline_audit(candidates)
    fairness = run_fairness_audit(candidates, domain, ranking)
    robustness = run_robustness_audit(candidates, candidates, candidates, domain)
    audit = build_audit_result(ranking.ranking_id, domain, timeline, fairness, robustness)

    cols = st.columns(5)
    cols[0].metric("排名领域", domain)
    cols[1].metric("候选人数", len(candidates))
    cols[2].metric("审计状态", audit.overall_conclusion.overall_audit_status)
    cols[3].metric("脱敏完成", "是")
    cols[4].metric("Critical", audit.overall_conclusion.critical_issue_count)

    st.subheader("时间线一致性")
    rows = []
    for cid, result in timeline["candidate_results"].items():
        rows.append(
            {
                "candidate_id": cid,
                "timeline_score": result["timeline_consistency_score"],
                "issue_count": result["issue_count"],
                "critical_issue_count": result["critical_issue_count"],
                "penalty_recommendation": result["penalty_recommendation"],
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    if timeline["detected_issues"]:
        st.warning("；".join(issue["description"] for issue in timeline["detected_issues"][:5]))

    st.subheader("敏感字段隔离审计")
    cols = st.columns(3)
    cols[0].metric("隔离检查", "通过" if fairness["sensitive_field_isolation_passed"] else "失败")
    cols[1].metric("最大分数变化", fairness["max_score_shift"])
    cols[2].metric("最大排名变化", fairness["max_rank_shift"])
    st.plotly_chart(fairness_shift_chart(fairness), use_container_width=True)

    st.subheader("排名稳定性")
    st.plotly_chart(robustness_rank_shift_chart(robustness), use_container_width=True)
    st.json(robustness["comparisons"])

    st.subheader("审计结论与限制")
    for line in audit.overall_conclusion.conclusion_summary:
        st.write(line)
    for item in audit.limitations:
        st.caption(item)
