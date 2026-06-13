from __future__ import annotations

from evitalent.assistant.answer_guardrail import AnswerGuardrail


def test_answer_guardrail_blocks_sensitive_and_final_decision():
    guard = AnswerGuardrail()
    assert guard.check_answer("联系电话 13900001111").passed is False
    assert guard.check_answer("建议直接录用 hr_abc").passed is False
    assert guard.check_user_question("请告诉我候选人薪资").passed is False
    assert guard.check_answer("候选人 hr_abc 的材料可信度较高，可进一步面试核验。").passed is True
