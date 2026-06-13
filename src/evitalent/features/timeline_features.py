from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from evitalent.models.extraction import CandidateExtraction, CareerRecord
from evitalent.utils import months_between, parse_year_month


@dataclass(frozen=True)
class TimelineIssue:
    issue_type: str
    severity: str
    message: str
    evidence_ids: list[str]


def career_months(record: CareerRecord) -> int | None:
    return months_between(record.start_date, record.end_date)


def total_work_years(candidate: CandidateExtraction) -> tuple[float, list[str], list[str]]:
    months = 0
    evidence_ids: list[str] = []
    warnings: list[str] = []
    for record in candidate.career_records:
        duration = career_months(record)
        if duration is None:
            warnings.append(f"日期精度不足或缺失: {record.title}")
            continue
        months += duration
        if record.evidence_id:
            evidence_ids.append(record.evidence_id)
    return round(months / 12, 2), evidence_ids, warnings


def relevant_experience_years(candidate: CandidateExtraction, domain: str) -> tuple[float | None, list[str]]:
    months = 0
    evidence_ids: list[str] = []
    for record in candidate.career_records:
        tags = {tag.lower() for tag in record.domain_tags}
        if domain.lower() in tags:
            duration = career_months(record)
            if duration is not None:
                months += duration
                evidence_ids.extend(record.evidence_ids)
    if months == 0 and candidate.domain_assessment_inputs.get(domain):
        years, ids, _ = total_work_years(candidate)
        return (years if years else None), ids
    return (round(months / 12, 2), sorted(set(evidence_ids))) if months else (None, [])


def median_tenure_months(candidate: CandidateExtraction) -> tuple[float | None, list[str]]:
    grouped: dict[str, list[CareerRecord]] = {}
    for record in candidate.career_records:
        grouped.setdefault(record.company, []).append(record)
    durations: list[int] = []
    evidence_ids: list[str] = []
    for company, records in grouped.items():
        starts = [parse_year_month(record.start_date) for record in records]
        ends = [parse_year_month(record.end_date) for record in records]
        if not all(starts):
            continue
        start = min(date for date in starts if date is not None)
        end_candidates = [date for date in ends if date is not None]
        end = max(end_candidates) if end_candidates else None
        months = months_between(start.isoformat()[:7], end.isoformat()[:7] if end else None)
        if months is not None:
            durations.append(months)
            evidence_ids.extend([record.evidence_id for record in records if record.evidence_id])
    if not durations:
        return None, []
    return float(median(durations)), sorted(set(evidence_ids))


def short_tenure_count(candidate: CandidateExtraction, threshold_months: int = 12) -> int:
    grouped: dict[str, int] = {}
    for record in candidate.career_records:
        duration = career_months(record)
        if duration is not None:
            grouped[record.company] = grouped.get(record.company, 0) + duration
    return sum(1 for duration in grouped.values() if duration < threshold_months)


def career_gap_months(candidate: CandidateExtraction) -> int:
    ranges = []
    for record in candidate.career_records:
        start = parse_year_month(record.start_date)
        end = parse_year_month(record.end_date)
        if start and end:
            ranges.append((start, end))
    ranges.sort()
    gaps = 0
    for (_, previous_end), (current_start, _) in zip(ranges, ranges[1:]):
        gap = (current_start.year - previous_end.year) * 12 + current_start.month - previous_end.month
        if gap > 1:
            gaps += gap - 1
    return gaps


def promotion_count(candidate: CandidateExtraction) -> tuple[int, list[str]]:
    terms = ("晋升", "升任", "提拔", "负责人", "总监", "经理", "主管")
    count = 0
    evidence_ids: list[str] = []
    for record in candidate.career_records:
        text = f"{record.title} {record.description}"
        if any(term in text for term in terms):
            count += 1
            if record.evidence_id:
                evidence_ids.append(record.evidence_id)
    return count, sorted(set(evidence_ids))


def detect_timeline_issues(candidate: CandidateExtraction) -> list[TimelineIssue]:
    issues: list[TimelineIssue] = []
    records = []
    for record in candidate.career_records:
        start = parse_year_month(record.start_date)
        end = parse_year_month(record.end_date)
        if not start or not end:
            issues.append(TimelineIssue("date_precision", "info", "日期精度不足或缺失", [record.evidence_id or ""]))
            continue
        records.append((start, end, record))
    records.sort(key=lambda item: item[0])
    for (_, previous_end, previous), (current_start, _, current) in zip(records, records[1:]):
        if current_start < previous_end:
            overlap = (previous_end.year - current_start.year) * 12 + previous_end.month - current_start.month
            severity = "error" if previous.company != current.company and overlap >= 6 else "warning"
            issues.append(
                TimelineIssue(
                    "full_time_overlap" if severity == "error" else "date_conflict",
                    severity,
                    "检测到任职时间重叠",
                    [previous.evidence_id or "", current.evidence_id or ""],
                )
            )
    return issues


def has_date_overlap(records: list[CareerRecord]) -> bool:
    ranges = []
    for record in records:
        start = parse_year_month(record.start_date)
        end = parse_year_month(record.end_date)
        if start and end:
            ranges.append((start, end, record.company))
    ranges.sort(key=lambda item: item[0])
    return any(current_start < previous_end and current_company != previous_company for (_, previous_end, previous_company), (current_start, _, current_company) in zip(ranges, ranges[1:]))
