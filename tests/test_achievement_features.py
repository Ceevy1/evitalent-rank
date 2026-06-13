from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.features.achievement_features import achievement_axis_score, score_achievement_event, scorable_achievements


def test_ab_grade_achievements_are_scorable():
    candidate = MockExtractor().extract("demo_hr_001")
    events = scorable_achievements(candidate)
    assert len(events) == 2
    assert all(score_achievement_event(event)["total"] > 0 for event in events)


def test_c_d_grade_do_not_enter_achievement_score():
    candidate = MockExtractor().extract("demo_hr_003")
    events = scorable_achievements(candidate)
    assert len(events) == 1
    score, ids, details = achievement_axis_score(candidate)
    assert "ev_hr3_ach2" not in ids
    assert score >= 0


def test_numeric_magnitude_normalization():
    candidate = MockExtractor().extract("demo_ecommerce_001")
    event = candidate.achievement_events[0]
    parts = score_achievement_event(event)
    assert 0 <= parts["result_magnitude"] <= 30
    assert parts["total"] <= 100
