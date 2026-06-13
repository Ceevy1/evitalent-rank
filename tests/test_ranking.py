from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import compute_bcs, rank_candidates


def _domain_candidates(domain):
    return [c for c in MockExtractor().load_all() if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]


def test_hr_and_production_have_three_candidates_and_rank():
    hr = rank_candidates(_domain_candidates("hr"), "hr")
    production = rank_candidates(_domain_candidates("production"), "production")
    assert len(hr.candidates) >= 3
    assert len(production.candidates) >= 3
    assert [item.rank_score for item in hr.candidates] == sorted([item.rank_score for item in hr.candidates], reverse=True)
    assert [item.rank_score for item in production.candidates] == sorted([item.rank_score for item in production.candidates], reverse=True)


def test_rank_score_formula():
    result = rank_candidates(_domain_candidates("hr"), "hr")
    item = result.candidates[0]
    expected_bcs = compute_bcs(item.axis_scores, "hr")
    expected = expected_bcs * (0.85 + 0.15 * item.eci / 100) - item.penalty
    assert item.bcs == expected_bcs
    assert item.rank_score == round(expected, 2)


def test_ranking_excludes_sensitive_fields_and_strengths_have_evidence():
    result = rank_candidates(_domain_candidates("production"), "production")
    dumped = result.model_dump_json()
    assert "salary_current" not in dumped
    assert "birth_year" not in dumped
    assert all(strength.evidence_ids for item in result.candidates for strength in item.top_strengths)
