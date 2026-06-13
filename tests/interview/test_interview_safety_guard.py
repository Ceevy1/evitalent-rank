from __future__ import annotations

from evitalent.interview.interview_safety_guard import InterviewSafetyGuard
from evitalent.interview.models import RecommendedQuestion


def _question(text: str) -> RecommendedQuestion:
    return RecommendedQuestion(
        question_id="q1",
        question_type="behavioral",
        question=text,
        why_ask="核验成果",
        evidence_basis="ev1",
        follow_up_probe="请补充说明。",
        expected_good_answer="说明背景、动作和结果。",
        red_flags=["无法说明口径"],
        related_competency="成果",
        suggested_score_dimension="成果验证",
    )


def test_safety_guard_blocks_sensitive_and_final_decision_text():
    guard = InterviewSafetyGuard()
    bad = [_question("请说明电话 13900001111"), _question("建议录用该候选人"), _question("请说明薪资情况")]
    safe, warnings = guard.filter_questions(bad)

    assert safe == []
    assert len(warnings) == 3


def test_safety_guard_allows_normal_question():
    safe, warnings = InterviewSafetyGuard().filter_questions([_question("请说明你在项目中的个人贡献。")])

    assert len(safe) == 1
    assert warnings == []
