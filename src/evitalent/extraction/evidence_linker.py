from __future__ import annotations

from typing import Any

from evitalent.models.extraction import CandidateExtraction, EvidenceGrade


def check_evidence_links(candidate: CandidateExtraction) -> dict[str, Any]:
    available = {item.evidence_id: item for item in candidate.evidence_items}
    missing: set[str] = set()
    invalid_scoring_links: list[dict[str, str]] = []
    warnings: list[str] = []

    def require(evidence_id: str | None, context: str) -> None:
        if evidence_id and evidence_id not in available:
            missing.add(evidence_id)
            invalid_scoring_links.append({"context": context, "evidence_id": evidence_id, "reason": "missing_evidence"})

    for record in candidate.education_records:
        require(record.evidence_id, f"education:{record.school}")

    for record in candidate.career_records:
        for evidence_id in record.evidence_ids:
            require(evidence_id, f"career:{record.title}")

    for record in candidate.project_records:
        for evidence_id in record.evidence_ids:
            require(evidence_id, f"project:{record.project_name}")

    for domain, assessment in candidate.domain_assessment_inputs.items():
        for evidence_id in assessment.evidence_ids:
            require(evidence_id, f"domain_assessment:{domain}")

    for event in candidate.achievement_events:
        require(event.evidence_id, f"achievement:{event.achievement_id}")
        evidence = available.get(event.evidence_id)
        if not evidence:
            continue
        if event.evidence_grade in {EvidenceGrade.A, EvidenceGrade.B} and not evidence.used_for_scoring:
            invalid_scoring_links.append(
                {
                    "context": f"achievement:{event.achievement_id}",
                    "evidence_id": event.evidence_id,
                    "reason": "scorable_achievement_requires_used_for_scoring_true",
                }
            )
        if event.evidence_grade == EvidenceGrade.D and evidence.used_for_scoring:
            invalid_scoring_links.append(
                {
                    "context": f"achievement:{event.achievement_id}",
                    "evidence_id": event.evidence_id,
                    "reason": "grade_d_evidence_cannot_enter_main_scoring",
                }
            )
        if event.evidence_grade == EvidenceGrade.D:
            warnings.append(f"{event.achievement_id} is grade D and must not enter main scoring")
        if not evidence.quote.strip():
            invalid_scoring_links.append(
                {
                    "context": f"achievement:{event.achievement_id}",
                    "evidence_id": event.evidence_id,
                    "reason": "evidence_quote_empty",
                }
            )

    return {
        "passed": not missing and not invalid_scoring_links,
        "missing_evidence_ids": sorted(missing),
        "invalid_scoring_links": invalid_scoring_links,
        "warnings": warnings,
    }


def validate_evidence_links(candidate: CandidateExtraction) -> list[str]:
    # Backward-compatible helper used by earlier scoring code.
    return check_evidence_links(candidate)["missing_evidence_ids"]
