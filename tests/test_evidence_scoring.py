from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction
from evitalent.scoring.axis_scorer import score_candidate_axes
from evitalent.scoring.evidence_scorer import score_eci


def test_eci_calculation_parts_present():
    candidate = MockExtractor().extract("demo_hr_001")
    features = score_candidate_axes(candidate, "hr")
    eci, parts = score_eci(candidate, features)
    assert 0 <= eci <= 100
    assert set(parts) == {"quantified_evidence_score", "traceability_score", "completeness_score", "consistency_score", "verifiability_score"}


def test_missing_evidence_lowers_eci():
    candidate = MockExtractor().extract("demo_hr_001")
    features = score_candidate_axes(candidate, "hr")
    base, _ = score_eci(candidate, features)
    payload = candidate.model_dump(mode="json")
    payload["achievement_events"][0]["evidence_id"] = "missing"
    broken = CandidateExtraction.model_validate(payload)
    lower, _ = score_eci(broken, features)
    assert lower < base


def test_sensitive_information_does_not_affect_eci():
    candidate = MockExtractor().extract("demo_hr_001")
    features = score_candidate_axes(candidate, "hr")
    base, _ = score_eci(candidate, features)
    payload = candidate.model_dump(mode="json")
    payload["sensitive_information"]["gender"] = "counterfactual"
    changed = CandidateExtraction.model_validate(payload)
    changed_eci, _ = score_eci(changed, features)
    assert changed_eci == base
