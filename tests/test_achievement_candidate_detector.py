from evitalent.achievement_detection import AchievementCandidateDetector
from evitalent.demo_samples import ECOMMERCE_MULTI_ACHIEVEMENT_TEXT, HR_MULTI_ACHIEVEMENT_TEXT, PRODUCTION_MULTI_ACHIEVEMENT_TEXT


def test_hr_sample_detects_five_candidates():
    assert len(AchievementCandidateDetector().detect(HR_MULTI_ACHIEVEMENT_TEXT)) == 5


def test_production_sample_detects_four_candidates():
    assert len(AchievementCandidateDetector().detect(PRODUCTION_MULTI_ACHIEVEMENT_TEXT)) == 4


def test_ecommerce_sample_detects_three_candidates():
    assert len(AchievementCandidateDetector().detect(ECOMMERCE_MULTI_ACHIEVEMENT_TEXT)) == 3
