from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.features.timeline_features import detect_timeline_issues, median_tenure_months, short_tenure_count
from evitalent.models.extraction import CandidateExtraction


def test_tenure_and_same_company_promotion_not_job_hop():
    candidate = MockExtractor().extract("demo_production_001")
    tenure, ids = median_tenure_months(candidate)
    assert tenure and tenure >= 60
    assert ids


def test_short_job_count_detects_short_tenure():
    candidate = MockExtractor().extract("demo_production_003")
    assert short_tenure_count(candidate) >= 1


def test_obvious_overlap_detected():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["career_records"][1]["start_date"] = "2018-01"
    broken = CandidateExtraction.model_validate(payload)
    issues = detect_timeline_issues(broken)
    assert any(issue.issue_type in {"date_conflict", "full_time_overlap"} for issue in issues)
