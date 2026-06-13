from __future__ import annotations

import re
from dataclasses import dataclass, field

from evitalent.assistant.access_policy import AccessPolicy

SAFE_BLOCKED_ANSWER = "本次回答包含可能需要保护的信息，系统已停止展示。请改为询问匿名分析结果或已核验能力依据。"
PRIVACY_REFUSAL = "为保护候选人隐私，系统不提供身份、联系方式、婚姻、薪资等信息。您可以询问匿名候选人的岗位匹配、成果依据或待核验事项。"
DECISION_LIMIT = "我不能直接作出录用、淘汰或晋升决定。可以基于匿名材料总结优势、风险和建议面试核验的问题。"


@dataclass(frozen=True)
class GuardrailResult:
    passed: bool
    text: str
    event_types: list[str] = field(default_factory=list)


class AnswerGuardrail:
    decision_patterns = [r"推荐录用", r"应该录用", r"直接录用", r"淘汰", r"不录用", r"晋升.*决定"]
    privacy_query_patterns = [r"姓名", r"电话", r"邮箱", r"婚姻", r"薪资", r"身份证", r"出生", r"住址"]

    def __init__(self, policy: AccessPolicy | None = None) -> None:
        self.policy = policy or AccessPolicy()

    def check_user_question(self, question: str) -> GuardrailResult:
        if any(re.search(pattern, question, re.IGNORECASE) for pattern in self.privacy_query_patterns):
            return GuardrailResult(False, PRIVACY_REFUSAL, ["privacy_query"])
        if self.policy.find_text_violations(question):
            return GuardrailResult(False, PRIVACY_REFUSAL, ["sensitive_user_input"])
        return GuardrailResult(True, question)

    def check_answer(self, answer: str) -> GuardrailResult:
        violations = self.policy.find_text_violations(answer)
        if violations:
            return GuardrailResult(False, SAFE_BLOCKED_ANSWER, violations)
        if any(re.search(pattern, answer, re.IGNORECASE) for pattern in self.decision_patterns):
            return GuardrailResult(False, DECISION_LIMIT, ["final_decision"])
        return GuardrailResult(True, answer)
