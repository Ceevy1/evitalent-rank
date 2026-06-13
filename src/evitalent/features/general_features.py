from __future__ import annotations

from evitalent.features.timeline_features import career_gap_months, median_tenure_months, promotion_count, relevant_experience_years, short_tenure_count, total_work_years
from evitalent.models.extraction import CandidateExtraction
from evitalent.models.features import ComputedFeatures
from evitalent.utils import clamp


DEGREE_BASE_SCORES = {
    "doctor": 95,
    "博士": 95,
    "master": 85,
    "硕士": 85,
    "bachelor": 75,
    "本科": 75,
    "associate": 55,
    "大专": 55,
    "专科": 55,
    "secondary": 40,
    "中专": 40,
    "高中": 40,
    "unknown": 50,
}


ROLE_LEVEL_SCORES = {
    "vp": 95,
    "副总": 92,
    "总监": 88,
    "负责人": 84,
    "经理": 76,
    "主管": 66,
    "工程师": 60,
    "专员": 55,
    "助理": 45,
}


DOMAIN_MAJOR_TERMS = {
    "hr": ("人力资源", "工商管理", "行政管理"),
    "brand": ("市场", "营销", "广告", "传播"),
    "ecommerce": ("电子商务", "市场", "营销"),
    "production": ("工业工程", "机械", "自动化", "质量", "食品"),
    "sales": ("工商管理", "市场", "营销"),
    "rd": ("研发", "食品", "材料", "生物", "化学", "计算机", "工程"),
}


def highest_degree_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    if not candidate.education_records:
        return 50.0, []
    best = 50.0
    ids: list[str] = []
    for record in candidate.education_records:
        text = f"{record.degree} {record.major}".lower()
        score = 50.0
        for term, value in DEGREE_BASE_SCORES.items():
            if term.lower() in text:
                score = float(value)
                break
        if score >= best:
            best = score
            ids = [record.evidence_id]
    return best, ids


def major_domain_match_score(candidate: CandidateExtraction, domain: str) -> tuple[float, list[str]]:
    terms = DOMAIN_MAJOR_TERMS.get(domain, ())
    ids: list[str] = []
    best = 50.0
    for record in candidate.education_records:
        text = f"{record.major} {record.degree}"
        if any(term in text for term in terms):
            best = 85.0
            ids = [record.evidence_id]
            break
    return best, ids


def highest_role_level_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    best = 50.0
    ids: list[str] = []
    for record in candidate.career_records:
        text = record.title.lower()
        score = next((float(value) for term, value in ROLE_LEVEL_SCORES.items() if term.lower() in text), 50.0)
        if score >= best:
            best = score
            ids = [record.evidence_id] if record.evidence_id else []
    return best, ids


def max_management_headcount(candidate: CandidateExtraction) -> tuple[int | None, list[str]]:
    values = [(record.management_headcount, record.evidence_id) for record in candidate.career_records if record.management_headcount is not None]
    if not values:
        return None, []
    count, evidence_id = max(values, key=lambda item: item[0] or 0)
    return count, [evidence_id] if evidence_id else []


def organization_scope_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    score = 50.0
    ids: list[str] = []
    keywords = ("多区域", "多工厂", "千人", "集团", "全国", "多产线", "重点客户", "研发中心")
    for record in candidate.career_records:
        text = " ".join(record.platform_evidence) + " " + record.description
        hits = sum(1 for key in keywords if key in text)
        if hits:
            score = max(score, min(100.0, 58.0 + hits * 12.0))
            if record.evidence_id:
                ids.append(record.evidence_id)
    return score, sorted(set(ids))


def project_count(candidate: CandidateExtraction) -> tuple[int, list[str]]:
    ids = [record.evidence_id for record in candidate.project_records if record.evidence_id]
    return len(candidate.project_records), ids


def zero_to_one_project_count(candidate: CandidateExtraction) -> tuple[int, list[str]]:
    terms = ("0到1", "从0到1", "新建", "上市", "建设", "搭建", "导入")
    count = 0
    ids: list[str] = []
    for record in candidate.project_records:
        text = f"{record.project_name} {record.description}"
        if any(term in text for term in terms):
            count += 1
            if record.evidence_id:
                ids.append(record.evidence_id)
    return count, ids


def resume_completeness_score(candidate: CandidateExtraction, domain: str) -> float:
    checks = [
        bool(candidate.education_records),
        len(candidate.career_records) >= 2,
        bool(candidate.project_records),
        bool(candidate.achievement_events),
        bool(candidate.domain_assessment_inputs.get(domain)),
    ]
    return sum(checks) / len(checks) * 100.0


def compute_general_features(candidate: CandidateExtraction, domain: str) -> ComputedFeatures:
    values = {}
    evidence = {}
    warnings: list[str] = []

    values["highest_degree_score"], evidence["highest_degree_score"] = highest_degree_score(candidate)
    values["major_domain_match_score"], evidence["major_domain_match_score"] = major_domain_match_score(candidate, domain)
    total_years, ids, date_warnings = total_work_years(candidate)
    values["total_work_years"] = total_years
    evidence["total_work_years"] = ids
    warnings.extend(date_warnings)
    relevant_years, ids = relevant_experience_years(candidate, domain)
    values["relevant_work_years"] = relevant_years if relevant_years is not None else 0.0
    evidence["relevant_work_years"] = ids
    values["relevant_year_ratio"] = 0.0 if total_years <= 0 else clamp((relevant_years or 0.0) / total_years * 100.0)
    values["median_tenure_months"], evidence["median_tenure_months"] = median_tenure_months(candidate)
    values["short_job_count"] = short_tenure_count(candidate)
    values["career_gap_months"] = career_gap_months(candidate)
    values["promotion_events"], evidence["promotion_events"] = promotion_count(candidate)
    values["promotion_speed_score"] = 50.0 if not values["promotion_events"] else clamp(60.0 + values["promotion_events"] * 12.0)
    values["highest_role_level_score"], evidence["highest_role_level_score"] = highest_role_level_score(candidate)
    headcount, ids = max_management_headcount(candidate)
    values["direct_report_max"] = headcount
    evidence["direct_report_max"] = ids
    values["organization_scope_score"], evidence["organization_scope_score"] = organization_scope_score(candidate)
    values["project_count"], evidence["project_count"] = project_count(candidate)
    values["zero_to_one_project_count"], evidence["zero_to_one_project_count"] = zero_to_one_project_count(candidate)
    values["resume_completeness_score"] = resume_completeness_score(candidate, domain)

    return ComputedFeatures(candidate_id=candidate.candidate_id, domain=domain, values=values, evidence_ids=evidence, warnings=warnings)


def education_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    return highest_degree_score(candidate)


def highest_level_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    return highest_role_level_score(candidate)
