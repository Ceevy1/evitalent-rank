from __future__ import annotations

from typing import Any, Optional

import yaml

from evitalent.interview.models import HighFitCondition
from evitalent.settings import PROJECT_ROOT


AXIS_LABELS = {
    "education": "教育基础",
    "match": "岗位匹配",
    "experience": "相关经验",
    "stability": "稳定性",
    "progression": "成长轨迹",
    "platform": "平台复杂度",
    "management": "管理能力",
    "competency": "专业能力",
    "achievement": "成果影响",
    "collaboration": "协同推动",
}

EVENT_LABELS = {
    "recruitment_delivery": "招聘交付能力",
    "recruitment_completion_rate": "招聘达成能力",
    "retention_improvement": "人才保留改善能力",
    "efficiency_improvement": "生产效率改善能力",
    "loss_reduction": "损耗与成本改善能力",
    "automation_upgrade": "自动化升级推动能力",
    "quality_improvement": "质量改善能力",
    "cost_reduction": "成本控制能力",
    "gmv_growth": "业务增长能力",
    "roi_improvement": "投放效率改善能力",
    "conversion_improvement": "转化提升能力",
    "revenue_growth": "收入增长能力",
    "product_launch": "产品上市推动能力",
    "patent_publication": "专利成果能力",
    "technology_transfer": "技术转化能力",
    "collection_performance": "回款管理能力",
    "channel_expansion": "渠道拓展能力",
}


def _get(payload: Any, name: str, default: Any = None) -> Any:
    if isinstance(payload, dict):
        return payload.get(name, default)
    return getattr(payload, name, default)


def _event_type(event: Any) -> str:
    value = _get(event, "event_type", "")
    return getattr(value, "value", value)


class CompetencyMatcher:
    def __init__(self, domain_weights: Optional[dict[str, Any]] = None) -> None:
        self.domain_weights = domain_weights or self._load_domain_weights()

    def match(self, analysis: Any, top_n: int = 5) -> list[HighFitCondition]:
        domain = _get(analysis, "target_domain") or _get(analysis, "domain") or _get(analysis, "folder_domain") or "hr"
        axis_scores = _get(analysis, "axis_scores", {}) or {}
        top_strengths = _get(analysis, "top_strengths", []) or []
        events = _get(analysis, "normalized_achievement_events", None) or _get(analysis, "achievement_events", []) or []
        careers = _get(analysis, "career_records", []) or []
        eci = float(_get(analysis, "eci", 0) or 0)
        weights = self.domain_weights.get(domain, {})

        candidates: list[tuple[float, HighFitCondition]] = []
        event_type_counts: dict[str, int] = {}
        evidence_by_event: dict[str, list[str]] = {}
        for event in events:
            event_type = _event_type(event)
            if not event_type:
                continue
            evidence_id = _get(event, "evidence_id")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            if evidence_id:
                evidence_by_event.setdefault(event_type, []).append(str(evidence_id))

        for axis, score in axis_scores.items():
            weight = float(weights.get(axis, 0))
            achievement_strength = min(1.0, len(events) / 4) if axis == "achievement" else 0.4
            responsibility_match = self._responsibility_match(axis, careers)
            evidence_confidence = min(max(eci / 100, 0), 1)
            fit_score = 0.35 * weight + 0.30 * achievement_strength + 0.20 * responsibility_match + 0.15 * evidence_confidence
            fit_score = max(fit_score, min(float(score or 0) / 100, 1) * 0.75)
            if float(score or 0) < 55 and axis != "achievement":
                continue
            candidates.append(
                (
                    fit_score,
                    HighFitCondition(
                        condition_id=f"axis_{axis}",
                        label=AXIS_LABELS.get(axis, axis),
                        fit_level=self._fit_level(fit_score),
                        basis=f"{AXIS_LABELS.get(axis, axis)}得分 {round(float(score or 0), 2)}，领域权重 {weight}",
                        evidence_ids=[],
                        confidence=round(min(fit_score, 1), 4),
                    ),
                )
            )

        for event_type, count in event_type_counts.items():
            achievement_strength = min(1.0, count / 2)
            confidence = min(max(eci / 100, 0.55), 1)
            fit_score = 0.35 * float(weights.get("achievement", 0)) + 0.30 * achievement_strength + 0.20 * 0.8 + 0.15 * confidence
            candidates.append(
                (
                    fit_score,
                    HighFitCondition(
                        condition_id=f"event_{event_type}",
                        label=EVENT_LABELS.get(event_type, f"{event_type}能力"),
                        fit_level=self._fit_level(fit_score),
                        basis=f"已核验结构化成果中包含 {count} 条 {EVENT_LABELS.get(event_type, event_type)} 相关事件",
                        related_event_type=event_type,
                        evidence_ids=evidence_by_event.get(event_type, []),
                        confidence=round(min(fit_score, 1), 4),
                    ),
                )
            )

        for index, strength in enumerate(top_strengths[:3]):
            label = _get(strength, "label", None) or _get(strength, "axis", None) or str(strength)
            if not label:
                continue
            axis = _get(strength, "axis", str(label))
            score = float(_get(strength, "score", 70) or 70)
            confidence = min(score / 100, 1)
            candidates.append(
                (
                    confidence,
                    HighFitCondition(
                        condition_id=f"strength_{index}_{axis}",
                        label=AXIS_LABELS.get(str(axis), str(label)),
                        fit_level=self._fit_level(confidence),
                        basis="来自排序解释中的核心优势标签",
                        evidence_ids=list(_get(strength, "evidence_ids", []) or []),
                        confidence=round(confidence, 4),
                    ),
                )
            )

        deduped: dict[str, tuple[float, HighFitCondition]] = {}
        for score, condition in candidates:
            current = deduped.get(condition.label)
            if current is None or score > current[0]:
                deduped[condition.label] = (score, condition)
        ordered = [item[1] for item in sorted(deduped.values(), key=lambda item: item[0], reverse=True)]
        return ordered[: max(3, min(top_n, 5))]

    def _load_domain_weights(self) -> dict[str, dict[str, float]]:
        payload = yaml.safe_load((PROJECT_ROOT / "config" / "domain_weights.yaml").read_text(encoding="utf-8"))
        return {domain: data.get("weights", {}) for domain, data in payload.get("domains", {}).items()}

    def _responsibility_match(self, axis: str, careers: list[Any]) -> float:
        text = " ".join(str(_get(career, "description", "")) + " " + " ".join(_get(career, "domain_tags", []) or []) for career in careers)
        keywords = {
            "management": ["团队", "管理", "负责人"],
            "achievement": ["提升", "下降", "完成", "增长", "达成"],
            "competency": ["专业", "系统", "运营", "生产", "研发", "招聘"],
            "collaboration": ["协同", "推动", "跨部门"],
            "platform": ["平台", "系统", "渠道"],
        }
        terms = keywords.get(axis, [AXIS_LABELS.get(axis, axis)])
        return 1.0 if any(term in text for term in terms) else 0.35

    def _fit_level(self, score: float) -> str:
        if score >= 0.72:
            return "high"
        if score >= 0.5:
            return "medium"
        return "low"
