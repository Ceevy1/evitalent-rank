from __future__ import annotations

from evitalent.models.extraction import CandidateExtraction
from evitalent.settings import PROJECT_ROOT
from evitalent.utils import clamp, load_yaml


def load_ontology() -> dict:
    return load_yaml(PROJECT_ROOT / "config" / "competency_ontology.yaml")


def domain_tag_coverage(candidate: CandidateExtraction, domain: str) -> tuple[float | None, list[str]]:
    assessment = candidate.domain_assessment_inputs.get(domain)
    if not assessment:
        return None, []
    ontology = load_ontology()
    expected = set(ontology["domains"][domain]["tags"])
    observed = set(assessment.competency_tags) | set(assessment.matched_tags)
    if not expected:
        return None, assessment.evidence_ids
    return len(observed & expected) / len(expected), assessment.evidence_ids


def domain_confidence(candidate: CandidateExtraction, domain: str) -> tuple[float, list[str]]:
    for item in candidate.candidate_profile.target_domain_candidates:
        if item.domain == domain:
            return item.confidence, item.evidence_ids
    return 0.0, []


def relevant_year_score(years: float | None) -> float:
    if years is None:
        return 50.0
    return clamp(45.0 + min(years, 8.0) / 8.0 * 55.0)


def domain_match_score(candidate: CandidateExtraction, domain: str, relevant_years: float | None = None) -> tuple[float, list[str]]:
    coverage, ids = domain_tag_coverage(candidate, domain)
    confidence, confidence_ids = domain_confidence(candidate, domain)
    tag_score = 50.0 if coverage is None else clamp(coverage * 100.0)
    year_score = relevant_year_score(relevant_years)
    score = 0.6 * year_score + 0.3 * tag_score + 0.1 * confidence * 100.0
    return round(clamp(score), 2), sorted(set(ids + confidence_ids))


def platform_score(candidate: CandidateExtraction) -> tuple[float, list[str]]:
    score = 50.0
    ids: list[str] = []
    keywords = ("上市", "集团", "多区域", "多品牌", "全国", "千人", "多工厂", "多产线", "重点客户", "研发中心", "天猫", "京东", "抖音")
    for record in candidate.career_records:
        text = " ".join(record.platform_evidence) + " " + record.description
        hits = sum(1 for key in keywords if key in text)
        if hits:
            score = max(score, clamp(55.0 + hits * 8.0))
            if record.evidence_id:
                ids.append(record.evidence_id)
    return round(score, 2), sorted(set(ids))


def collaboration_score(candidate: CandidateExtraction, domain: str) -> tuple[float, list[str]]:
    assessment = candidate.domain_assessment_inputs.get(domain)
    if not assessment:
        return 50.0, []
    objective = [tag for tag in assessment.collaboration_tags if tag not in {"沟通能力强", "情商好"}]
    if not objective:
        return 50.0, []
    return round(clamp(50.0 + len(set(objective)) * 12.0), 2), assessment.evidence_ids


def competency_score(candidate: CandidateExtraction, domain: str) -> tuple[float, list[str]]:
    coverage, ids = domain_tag_coverage(candidate, domain)
    if coverage is None:
        return 50.0, []
    return round(clamp(45.0 + coverage * 70.0), 2), ids
