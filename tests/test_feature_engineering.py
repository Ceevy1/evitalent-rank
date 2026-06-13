from evitalent.scoring.axis_scorer import AXES, score_candidate_axes


def test_feature_engineering_axis_scores(candidates):
    features = score_candidate_axes(candidates[0], candidates[0].candidate_profile.target_domains[0])
    assert set(features.axis_scores) == set(AXES)
    assert all(0 <= score <= 100 for score in features.axis_scores.values())
    assert "max_management_headcount" in features.metrics

