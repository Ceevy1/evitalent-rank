from evitalent.scoring.ranker import rank_candidates


def test_scoring_outputs_range_and_sorting(candidates):
    result = rank_candidates(candidates, "hr")
    assert len(result.results) >= 3
    scores = [item.rank_score for item in result.results]
    assert scores == sorted(scores, reverse=True)
    for item in result.results:
        assert 0 <= item.bcs <= 100
        assert 0 <= item.eci <= 100
        assert item.penalty <= 8


def test_sensitive_fields_do_not_change_main_score(candidates):
    baseline = rank_candidates(candidates, "hr")
    for candidate in candidates:
        candidate.sensitive_information.gender = "counterfactual"
    changed = rank_candidates(candidates, "hr")
    assert [item.rank_score for item in baseline.results] == [item.rank_score for item in changed.results]

