from __future__ import annotations

from evitalent.extraction.evidence_linker import check_evidence_links
from evitalent.features.timeline_features import detect_timeline_issues
from evitalent.models.extraction import CandidateExtraction, EvidenceGrade
from evitalent.models.ranking import CandidateFeatures
from evitalent.utils import clamp


def score_eci(candidate: CandidateExtraction, features: CandidateFeatures) -> tuple[float, dict[str, float]]:
    events = candidate.achievement_events
    quantified = [event for event in events if event.metric_value is not None and event.evidence_grade in {EvidenceGrade.A, EvidenceGrade.B}]
    event_types = {event.event_type.value for event in quantified}
    quantified_evidence_score = clamp(len(quantified) * 25.0 + len(event_types) * 10.0)

    link_result = check_evidence_links(candidate)
    total_axis_links = sum(len(ids) for ids in features.evidence_ids_by_axis.values())
    traceability_score = 100.0 if total_axis_links else 50.0
    traceability_score = clamp(traceability_score - len(link_result["missing_evidence_ids"]) * 15.0 - len(link_result["invalid_scoring_links"]) * 12.0)

    complete_parts = [
        bool(candidate.education_records),
        len(candidate.career_records) >= 2,
        bool(candidate.project_records),
        bool(candidate.achievement_events),
        bool(candidate.domain_assessment_inputs.get(features.domain)),
    ]
    completeness_score = sum(complete_parts) / len(complete_parts) * 100.0
    missing_axis_count = sum(1 for ids in features.evidence_ids_by_axis.values() if not ids)
    completeness_score = clamp(completeness_score - missing_axis_count * 4.0)

    issues = detect_timeline_issues(candidate)
    consistency_score = 100.0
    for issue in issues:
        if issue.severity == "error":
            consistency_score -= 30.0
        elif issue.severity == "warning":
            consistency_score -= 12.0
        else:
            consistency_score -= 4.0
    consistency_score = clamp(consistency_score)

    verifiable = 0
    for event in candidate.achievement_events:
        parts = [
            event.metric_value is not None,
            event.period_months is not None,
            bool(event.metric_name),
            bool(event.candidate_contribution),
        ]
        if sum(parts) >= 3 and event.evidence_grade in {EvidenceGrade.A, EvidenceGrade.B}:
            verifiable += 1
    verifiability_score = clamp(verifiable / max(1, len(candidate.achievement_events)) * 100.0)

    parts = {
        "quantified_evidence_score": round(quantified_evidence_score, 2),
        "traceability_score": round(traceability_score, 2),
        "completeness_score": round(completeness_score, 2),
        "consistency_score": round(consistency_score, 2),
        "verifiability_score": round(verifiability_score, 2),
    }
    eci = (
        0.30 * parts["quantified_evidence_score"]
        + 0.25 * parts["traceability_score"]
        + 0.20 * parts["completeness_score"]
        + 0.15 * parts["consistency_score"]
        + 0.10 * parts["verifiability_score"]
    )
    return round(clamp(eci), 2), parts
