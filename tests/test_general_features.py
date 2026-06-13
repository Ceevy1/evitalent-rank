from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.features.general_features import compute_general_features, highest_degree_score


def test_work_years_and_degree_mapping():
    candidate = MockExtractor().extract("demo_hr_001")
    features = compute_general_features(candidate, "hr")
    assert features.get_number("total_work_years") >= 9
    assert features.get_number("relevant_work_years") >= 9
    score, ids = highest_degree_score(candidate)
    assert score == 85
    assert ids


def test_missing_fields_do_not_crash():
    candidate = MockExtractor().extract("demo_hr_003")
    features = compute_general_features(candidate, "hr")
    assert features.values["direct_report_max"] is None
    assert features.get_number("resume_completeness_score") > 0
