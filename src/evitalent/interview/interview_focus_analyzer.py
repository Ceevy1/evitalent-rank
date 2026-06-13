from __future__ import annotations

from typing import Any

from evitalent.interview.competency_matcher import _event_type, _get
from evitalent.interview.models import HighFitCondition, InterviewFocusArea


SCALE_UNITS = {"人", "万元", "亿元", "%", "套", "个"}


class InterviewFocusAnalyzer:
    def analyze(self, conditions: list[HighFitCondition], analysis: Any) -> list[InterviewFocusArea]:
        events = _get(analysis, "normalized_achievement_events", None) or _get(analysis, "achievement_events", []) or []
        risk_flags = list(_get(analysis, "risk_flags", []) or [])
        eci = float(_get(analysis, "eci", 0) or 0)
        focus: list[InterviewFocusArea] = []

        for condition in conditions[:2]:
            focus.append(
                InterviewFocusArea(
                    focus_id=f"strength_{condition.condition_id}",
                    focus_name=f"验证{condition.label}",
                    focus_type="strength_validation",
                    reason=f"该能力是当前候选人与目标岗位的主要契合条件：{condition.basis}",
                    related_evidence_ids=condition.evidence_ids,
                    priority="high" if condition.fit_level == "high" else "medium",
                )
            )

        for index, event in enumerate(events[:3]):
            event_type = _event_type(event) or "achievement"
            evidence_id = _get(event, "evidence_id")
            value = _get(event, "metric_value")
            unit = _get(event, "unit", "")
            focus.append(
                InterviewFocusArea(
                    focus_id=f"depth_{index}_{event_type}",
                    focus_name=f"深挖{event_type}成果",
                    focus_type="depth_probe",
                    reason="该成果已进入结构化结果，建议核验候选人的真实角色、数据口径和贡献边界。",
                    related_evidence_ids=[str(evidence_id)] if evidence_id else [],
                    priority="high" if value not in {None, 0} else "medium",
                )
            )
            if value not in {None, 0} or str(unit) in SCALE_UNITS:
                focus.append(
                    InterviewFocusArea(
                        focus_id=f"scale_{index}_{event_type}",
                        focus_name=f"确认{event_type}成果规模",
                        focus_type="scale_context",
                        reason="成果包含数量、比例、金额、产能或团队规模信息，需要确认统计口径和业务背景。",
                        related_evidence_ids=[str(evidence_id)] if evidence_id else [],
                        priority="medium",
                    )
                )

        if conditions:
            focus.append(
                InterviewFocusArea(
                    focus_id="transferability_main",
                    focus_name="验证能力迁移性",
                    focus_type="transferability",
                    reason="候选人的过往成果需要确认是否能迁移到当前岗位目标、资源条件和组织环境。",
                    related_evidence_ids=conditions[0].evidence_ids,
                    priority="medium",
                )
            )

        if eci < 70:
            risk_flags.append("材料可信度偏低，建议面试核验")
        for index, flag in enumerate(risk_flags[:3]):
            focus.append(
                InterviewFocusArea(
                    focus_id=f"risk_{index}",
                    focus_name="核验待确认事项",
                    focus_type="risk_check",
                    reason=str(flag),
                    related_evidence_ids=[],
                    priority="high",
                )
            )

        deduped: dict[str, InterviewFocusArea] = {}
        for item in focus:
            deduped.setdefault(f"{item.focus_type}:{item.focus_name}:{item.reason}", item)
        result = list(deduped.values())[:8]
        while len(result) < 3:
            result.append(
                InterviewFocusArea(
                    focus_id=f"default_{len(result)}",
                    focus_name="补充核验岗位匹配",
                    focus_type="risk_check",
                    reason="当前安全摘要中的证据不足，建议面试核验候选人与岗位要求的匹配度。",
                    priority="medium",
                )
            )
        return result
