from __future__ import annotations

from copy import deepcopy

from evitalent.features.achievement_features import achievement_axis_score, quantified_achievement_count
from evitalent.features.domain_features import collaboration_score, competency_score, domain_match_score, platform_score
from evitalent.features.general_features import compute_general_features
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.ranking import CandidateFeatures
from evitalent.settings import PROJECT_ROOT
from evitalent.utils import clamp, load_yaml


AXES = [
    "education",
    "match",
    "experience",
    "stability",
    "progression",
    "platform",
    "management",
    "competency",
    "achievement",
    "collaboration",
]


def load_domain_weight_config(path=None) -> dict:
    cfg = load_yaml(path or PROJECT_ROOT / "config" / "domain_weights.yaml")
    for domain, item in cfg["domains"].items():
        weights = item["weights"]
        missing = set(AXES) - set(weights)
        if missing:
            raise ValueError(f"Domain {domain} missing weights: {sorted(missing)}")
        total = sum(float(weights[axis]) for axis in AXES)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Domain {domain} weights must sum to 1.0, got {total}")
    return cfg


def _stability_score(median_months) -> float:
    if median_months is None:
        return 50.0
    if median_months < 12:
        return 35.0
    if median_months < 24:
        return 55.0
    if median_months < 36:
        return 70.0
    if median_months < 60:
        return 85.0
    return 92.0


def score_candidate_axes(candidate: CandidateExtraction, domain: str) -> CandidateFeatures:
    load_domain_weight_config()
    features = compute_general_features(candidate, domain)
    values = features.values
    evidence = deepcopy(features.evidence_ids)
    risk_flags: list[str] = list(features.warnings)

    axis_scores: dict[str, float] = {}
    evidence_by_axis: dict[str, list[str]] = {}

    education = clamp(float(values["highest_degree_score"]) + max(0.0, float(values["major_domain_match_score"]) - 50.0) * 0.2)
    axis_scores["education"] = education
    evidence_by_axis["education"] = sorted(set(evidence.get("highest_degree_score", []) + evidence.get("major_domain_match_score", [])))

    relevant_years = float(values.get("relevant_work_years") or 0.0)
    axis_scores["match"], evidence_by_axis["match"] = domain_match_score(candidate, domain, relevant_years)
    if axis_scores["match"] < 60:
        risk_flags.append("专业匹配证据不足")

    project_complexity = min(15.0, float(values.get("project_count") or 0) * 5.0 + float(values.get("zero_to_one_project_count") or 0) * 5.0)
    axis_scores["experience"] = clamp(45.0 + min(relevant_years, 8.0) / 8.0 * 35.0 + (float(values["highest_role_level_score"]) - 50.0) * 0.25 + project_complexity)
    evidence_by_axis["experience"] = sorted(set(evidence.get("relevant_work_years", []) + evidence.get("highest_role_level_score", []) + evidence.get("project_count", [])))
    if relevant_years <= 0:
        risk_flags.append("相关年限证据不足")

    axis_scores["stability"] = _stability_score(values.get("median_tenure_months"))
    evidence_by_axis["stability"] = evidence.get("median_tenure_months", [])
    if values.get("short_job_count", 0) and int(values.get("short_job_count") or 0) >= 2:
        risk_flags.append("短期任职次数较多")

    promotion_events = float(values.get("promotion_events") or 0)
    axis_scores["progression"] = 50.0 if promotion_events == 0 else clamp(55.0 + promotion_events * 12.0 + (float(values["highest_role_level_score"]) - 50.0) * 0.3)
    evidence_by_axis["progression"] = sorted(set(evidence.get("promotion_events", []) + evidence.get("highest_role_level_score", [])))

    axis_scores["platform"], evidence_by_axis["platform"] = platform_score(candidate)

    headcount = values.get("direct_report_max")
    values["max_management_headcount"] = headcount
    if headcount is None:
        axis_scores["management"] = 50.0
        evidence_by_axis["management"] = evidence.get("organization_scope_score", [])
    else:
        axis_scores["management"] = clamp(50.0 + min(float(headcount), 80.0) / 80.0 * 40.0 + (float(values["organization_scope_score"]) - 50.0) * 0.2)
        evidence_by_axis["management"] = sorted(set(evidence.get("direct_report_max", []) + evidence.get("organization_scope_score", [])))

    axis_scores["competency"], evidence_by_axis["competency"] = competency_score(candidate, domain)

    achievement_score, achievement_ids, achievement_details = achievement_axis_score(candidate)
    axis_scores["achievement"] = achievement_score
    evidence_by_axis["achievement"] = achievement_ids
    values["achievement_event_scores"] = str(achievement_details)
    count, _ = quantified_achievement_count(candidate)
    values["quantified_achievement_count"] = count
    if count == 0:
        risk_flags.append("量化成果缺失")

    axis_scores["collaboration"], evidence_by_axis["collaboration"] = collaboration_score(candidate, domain)
    values["cross_function_events"] = len(candidate.domain_assessment_inputs.get(domain).collaboration_tags) if candidate.domain_assessment_inputs.get(domain) else 0
    values["leadership_evidence_score"] = axis_scores["collaboration"]
    values["company_platform_score"] = axis_scores["platform"]

    confidence = next((item.confidence for item in candidate.candidate_profile.target_domain_candidates if item.domain == domain), 0.0)
    if confidence < 0.7:
        risk_flags.append("领域判断置信度低")

    for axis in AXES:
        axis_scores[axis] = round(clamp(axis_scores[axis]), 2)
        if not evidence_by_axis.get(axis):
            risk_flags.append(f"{axis} 证据不足")

    return CandidateFeatures(
        candidate_id=candidate.candidate_id,
        display_id=candidate.candidate_profile.display_id,
        domain=domain,
        axis_scores=axis_scores,
        evidence_ids_by_axis=evidence_by_axis,
        metrics=values,
        risk_flags=sorted(set(risk_flags)),
    )
