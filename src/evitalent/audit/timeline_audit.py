from __future__ import annotations

from evitalent.models.audit import AuditIssue, TimelineAuditResult
from evitalent.models.extraction import CandidateExtraction, CareerRecord
from evitalent.utils import parse_year_month


NON_FULL_TIME_TERMS = ("顾问", "兼职", "项目制", "咨询", "外部专家")


def _months_diff(start, end) -> int:
    return (end.year - start.year) * 12 + end.month - start.month


def _is_non_full_time(record: CareerRecord) -> bool:
    text = f"{record.title} {record.description}"
    return any(term in text for term in NON_FULL_TIME_TERMS)


def _career_ranges(candidate: CandidateExtraction):
    ranges = []
    issues: list[AuditIssue] = []
    for record in candidate.career_records:
        start = parse_year_month(record.start_date)
        end = parse_year_month(record.end_date)
        evidence_ids = [eid for eid in record.evidence_ids if eid]
        if not start or not end:
            issues.append(
                AuditIssue(
                    issue_type="date_precision",
                    severity="info",
                    description="工作经历日期格式不可解析或精度不足，建议人工核验。",
                    candidate_id=candidate.candidate_id,
                    related_evidence_ids=evidence_ids,
                )
            )
            continue
        if start > end:
            issues.append(
                AuditIssue(
                    issue_type="invalid_date_range",
                    severity="critical",
                    description="工作经历开始日期晚于结束日期。",
                    candidate_id=candidate.candidate_id,
                    related_evidence_ids=evidence_ids,
                )
            )
        ranges.append((start, end, record))
    return ranges, issues


def audit_candidate_timeline(candidate: CandidateExtraction) -> TimelineAuditResult:
    ranges, issues = _career_ranges(candidate)
    ranges.sort(key=lambda item: item[0])
    related: set[str] = set()

    for (_, previous_end, previous), (current_start, _, current) in zip(ranges, ranges[1:]):
        if current_start >= previous_end:
            continue
        ids = sorted(set(previous.evidence_ids + current.evidence_ids))
        related.update(ids)
        if previous.company == current.company:
            continue
        if _is_non_full_time(previous) or _is_non_full_time(current):
            issues.append(
                AuditIssue(
                    issue_type="explained_overlap",
                    severity="info",
                    description="存在时间重叠，但记录显示顾问、兼职或项目制，未视为严重异常。",
                    candidate_id=candidate.candidate_id,
                    related_evidence_ids=ids,
                )
            )
            continue
        overlap_months = _months_diff(current_start, previous_end)
        issues.append(
            AuditIssue(
                issue_type="full_time_overlap",
                severity="critical" if overlap_months >= 6 else "warning",
                description="检测到无法解释的全职任职时间重叠。",
                candidate_id=candidate.candidate_id,
                related_evidence_ids=ids,
            )
        )

    for project in candidate.project_records:
        ps = parse_year_month(project.start_date)
        pe = parse_year_month(project.end_date)
        if not ps or not pe:
            continue
        if not any(start <= ps and pe <= end for start, end, _ in ranges):
            ids = [eid for eid in project.evidence_ids if eid]
            related.update(ids)
            issues.append(
                AuditIssue(
                    issue_type="project_outside_tenure",
                    severity="warning",
                    description=f"项目 {project.project_name} 时间不在任职期间内。",
                    candidate_id=candidate.candidate_id,
                    related_evidence_ids=ids,
                )
            )

    declared = candidate.candidate_profile.total_years_experience
    if declared is not None and ranges:
        months = sum(max(0, _months_diff(start, end)) for start, end, _ in ranges)
        calculated = months / 12
        if abs(float(declared) - calculated) > 2:
            issues.append(
                AuditIssue(
                    issue_type="experience_year_mismatch",
                    severity="warning",
                    description="概要声明的工作年限与经历计算年限差异超过 2 年。",
                    candidate_id=candidate.candidate_id,
                    related_evidence_ids=[],
                )
            )

    critical = sum(1 for issue in issues if issue.severity == "critical")
    warning = sum(1 for issue in issues if issue.severity == "warning")
    score = max(0.0, 100.0 - critical * 35.0 - warning * 15.0)
    penalty = 6.0 if any(issue.issue_type == "full_time_overlap" and issue.severity == "critical" for issue in issues) else 0.0
    if not penalty and any(issue.severity == "warning" for issue in issues):
        penalty = 3.0
    return TimelineAuditResult(
        issue_count=len(issues),
        critical_issue_count=critical,
        timeline_consistency_score=round(score, 2),
        detected_issues=issues,
        penalty_recommendation=penalty,
        related_evidence_ids=sorted(related),
    )


def run_timeline_audit(candidate: CandidateExtraction | list[CandidateExtraction]) -> dict:
    candidates = candidate if isinstance(candidate, list) else [candidate]
    results = {item.candidate_id: audit_candidate_timeline(item).model_dump(mode="json") for item in candidates}
    all_issues = [issue for result in results.values() for issue in result["detected_issues"]]
    critical = sum(1 for issue in all_issues if issue["severity"] == "critical")
    return {
        "candidate_results": results,
        "issue_count": len(all_issues),
        "critical_issue_count": critical,
        "timeline_consistency_score": round(sum(r["timeline_consistency_score"] for r in results.values()) / max(1, len(results)), 2),
        "detected_issues": all_issues,
        "penalty_recommendation": max((r["penalty_recommendation"] for r in results.values()), default=0.0),
        "related_evidence_ids": sorted({eid for r in results.values() for eid in r["related_evidence_ids"]}),
        # Backward-compatible fields.
        "candidate_id": candidates[0].candidate_id if len(candidates) == 1 else None,
        "issues": all_issues,
        "penalty_recommended": bool(all_issues),
    }
