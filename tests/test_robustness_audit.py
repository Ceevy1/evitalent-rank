from evitalent.audit.robustness_audit import rank_shift_metrics, run_robustness_audit, top_k_consistency
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates


def _hr_candidates():
    return [c for c in MockExtractor().load_all() if any(item.domain == "hr" for item in c.candidate_profile.target_domain_candidates)]


def test_top_k_consistency_and_mean_shift():
    candidates = _hr_candidates()
    result = rank_candidates(candidates, "hr")
    assert top_k_consistency(result, result, 3) == 1.0
    assert rank_shift_metrics(result, result) == (0.0, 0)


def test_robustness_single_candidate_no_crash():
    candidate = _hr_candidates()[:1]
    audit = run_robustness_audit(candidate, candidate, candidate, "hr")
    assert audit["comparisons"]["fact_only_text"]["top_k_consistency"] is None


def test_robustness_warning_when_rank_changes():
    candidates = _hr_candidates()
    reversed_candidates = list(reversed(candidates))
    # Different input order alone should not change deterministic ranking for this data.
    audit = run_robustness_audit(candidates, reversed_candidates, reversed_candidates, "hr")
    assert "comparisons" in audit
