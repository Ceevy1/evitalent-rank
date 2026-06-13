from evitalent.audit.fairness_audit import run_fairness_audit
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction


def test_fairness_audit_no_rank_shift(candidates):
    audit = run_fairness_audit(candidates, "hr")
    assert audit["mean_rank_shift"] == 0
    assert audit["max_rank_shift"] == 0


def test_sensitive_fields_do_not_affect_rank_score():
    candidates = [c for c in MockExtractor().load_all() if any(item.domain == "hr" for item in c.candidate_profile.target_domain_candidates)]
    audit = run_fairness_audit(candidates, "hr")
    assert audit["max_score_shift"] == 0
    assert audit["candidate_rank_shift"]
    assert all(value == 0 for value in audit["candidate_rank_shift"].values())


def test_sensitive_field_in_scoring_input_fails():
    candidate = MockExtractor().extract("demo_hr_001")
    payload = candidate.model_dump(mode="json")
    payload["domain_assessment_inputs"]["hr"]["gender"] = "counterfactual_gender"
    changed = CandidateExtraction.model_validate(payload)
    audit = run_fairness_audit([changed], "hr")
    assert audit["fairness_audit_status"] == "failed"
    assert any(issue["issue_type"] == "sensitive_field_in_scoring_input" for issue in audit["detected_issues"])
