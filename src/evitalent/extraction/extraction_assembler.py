from __future__ import annotations

from datetime import datetime, timezone

from evitalent.models.extraction import CandidateExtraction
from evitalent.models.normalized_achievement import NormalizedAchievementEvent


def assemble_candidate_extraction(
    document_id: str,
    candidate_id: str,
    domain: str,
    redacted_text: str,
    normalized_events: list[NormalizedAchievementEvent],
) -> CandidateExtraction:
    evidence_items = [
        {
            "evidence_id": "ev_edu_001",
            "section": "教育经历",
            "quote": "教育经历：脱敏演示样例",
            "fact_type": "education",
            "used_for_scoring": True,
        },
        {
            "evidence_id": "ev_job_001",
            "section": "工作经历",
            "quote": redacted_text[:180],
            "fact_type": "career",
            "used_for_scoring": True,
        },
        {
            "evidence_id": "ev_project_001",
            "section": "项目经历",
            "quote": redacted_text[:180],
            "fact_type": "project",
            "used_for_scoring": True,
        },
    ]
    achievement_events = []
    for event in normalized_events:
        evidence_items.append(
            {
                "evidence_id": event.evidence_id,
                "section": "工作业绩",
                "quote": event.evidence_quote,
                "fact_type": "achievement",
                "used_for_scoring": bool(event.eligible_for_core_achievement_score and event.grounding_status == "passed"),
            }
        )
        if event.eligible_for_core_achievement_score and event.grounding_status == "passed":
            achievement_events.append(
                {
                    "achievement_id": event.achievement_id,
                    "event_type": event.event_type,
                    "metric_name": event.normalized_metric_name,
                    "metric_value": event.metric_value,
                    "metric_value_upper": event.metric_value_upper,
                    "unit": event.unit,
                    "direction": event.direction,
                    "period_months": event.period_months,
                    "approximate": event.approximate,
                    "lower_bound": event.lower_bound,
                    "candidate_contribution": "负责/推动相关工作",
                    "evidence_grade": "A" if event.metric_value is not None else "C",
                    "evidence_id": event.evidence_id,
                    "raw_achievement_text": event.raw_achievement_text,
                    "normalization_rule_id": event.normalization_rule_id,
                }
            )

    if not achievement_events:
        achievement_events.append(
            {
                "achievement_id": "ACH_NEEDS_REVIEW",
                "event_type": "other",
                "metric_name": "待人工复核",
                "metric_value": None,
                "metric_value_upper": None,
                "unit": None,
                "direction": "unknown",
                "period_months": None,
                "approximate": False,
                "lower_bound": False,
                "candidate_contribution": "待人工复核",
                "evidence_grade": "C",
                "evidence_id": evidence_items[-1]["evidence_id"],
            }
        )

    domain_tags = [domain]
    payload = {
        "schema_version": "1.0.0",
        "document_id": document_id,
        "candidate_id": candidate_id,
        "parse_metadata": {
            "source_type": "redacted_text",
            "parsed_at": datetime.now(timezone.utc).isoformat(),
            "parser_version": "hybrid_v1",
        },
        "sensitive_information": {
            "name_detected": False,
            "gender": None,
            "birth_year": None,
            "marital_status": None,
            "salary_current": None,
            "salary_expected": None,
            "location": None,
            "masked_for_scoring": True,
        },
        "candidate_profile": {
            "display_id": candidate_id,
            "target_domain_candidates": [{"domain": domain, "confidence": 0.9, "evidence_ids": ["ev_job_001"]}],
            "summary": "混合抽取演示候选人",
            "highest_degree": "bachelor",
            "major": "管理类",
            "total_years_experience": 6,
            "current_level": "manager",
        },
        "education_records": [
            {"school": "脱敏大学", "degree": "bachelor", "major": "管理类", "start_date": "2012", "end_date": "2016", "evidence_id": "ev_edu_001"}
        ],
        "career_records": [
            {
                "company": "脱敏公司A",
                "title": "经理",
                "start_date": "2018-01",
                "end_date": "2021-12",
                "description": redacted_text[:240],
                "domain_tags": domain_tags,
                "management_headcount": 20,
                "platform_evidence": ["多部门协同"],
                "evidence_ids": ["ev_job_001"],
            },
            {
                "company": "脱敏公司B",
                "title": "高级经理",
                "start_date": "2022-01",
                "end_date": "2025-12",
                "description": redacted_text[:240],
                "domain_tags": domain_tags,
                "management_headcount": 30,
                "platform_evidence": ["流程优化"],
                "evidence_ids": ["ev_job_001"],
            },
        ],
        "project_records": [
            {
                "project_name": "成果改善项目",
                "start_date": "2022-01",
                "end_date": "2025-12",
                "description": redacted_text[:240],
                "domain_tags": domain_tags,
                "evidence_ids": ["ev_project_001"],
            }
        ],
        "achievement_events": achievement_events,
        "domain_assessment_inputs": {
            domain: {
                "domain": domain,
                "matched_tags": domain_tags,
                "competency_tags": domain_tags + ["流程优化", "量化成果"],
                "collaboration_tags": ["跨部门协同", "组织推动"],
                "evidence_ids": [item["evidence_id"] for item in evidence_items],
                "notes": "由混合抽取管线生成",
            }
        },
        "evidence_items": evidence_items,
        "quality_flags": [],
        "llm_metadata": {"provider": "hybrid", "model_name": "hybrid_python_llm_v1", "temperature": 0},
    }
    return CandidateExtraction.model_validate(payload)
