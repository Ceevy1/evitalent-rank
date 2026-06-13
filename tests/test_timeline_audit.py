from evitalent.audit.timeline_audit import run_timeline_audit
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction


def test_normal_timeline_has_no_critical_issue():
    candidate = MockExtractor().extract("demo_production_001")
    audit = run_timeline_audit(candidate)
    assert audit["critical_issue_count"] == 0


def test_same_company_promotion_not_overlap_issue():
    candidate = MockExtractor().extract("demo_production_001")
    payload = candidate.model_dump(mode="json")
    payload["career_records"][1]["company"] = payload["career_records"][0]["company"]
    payload["career_records"][1]["start_date"] = payload["career_records"][0]["start_date"]
    changed = CandidateExtraction.model_validate(payload)
    audit = run_timeline_audit(changed)
    assert not any(issue["issue_type"] == "full_time_overlap" for issue in audit["detected_issues"])


def test_full_time_overlap_is_detected():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["career_records"][1]["start_date"] = payload["career_records"][0]["start_date"]
    changed = CandidateExtraction.model_validate(payload)
    audit = run_timeline_audit(changed)
    assert any(issue["issue_type"] == "full_time_overlap" for issue in audit["detected_issues"])
    assert audit["penalty_recommendation"] >= 3


def test_project_outside_tenure_is_detected():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["project_records"][0]["start_date"] = "1999-01"
    payload["project_records"][0]["end_date"] = "1999-06"
    changed = CandidateExtraction.model_validate(payload)
    audit = run_timeline_audit(changed)
    assert any(issue["issue_type"] == "project_outside_tenure" for issue in audit["detected_issues"])
