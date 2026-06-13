from __future__ import annotations

import re

from evitalent.interview.models import InterviewRecommendation, RecommendedQuestion


BLOCK_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\d{17}[\dXx]"),
    re.compile(r"(出生日期|年龄|婚姻|家庭情况|薪资|原始文件名|私有路径|建议录用|建议淘汰)"),
]


class InterviewSafetyGuard:
    def is_safe_text(self, text: str) -> bool:
        return not any(pattern.search(text or "") for pattern in BLOCK_PATTERNS)

    def filter_questions(self, questions: list[RecommendedQuestion]) -> tuple[list[RecommendedQuestion], list[str]]:
        safe: list[RecommendedQuestion] = []
        warnings: list[str] = []
        for question in questions:
            payload = question.model_dump_json() if hasattr(question, "model_dump_json") else str(question)
            if self.is_safe_text(payload):
                safe.append(question)
            else:
                warnings.append(f"问题 {question.question_id} 因包含敏感或最终决策表述被移除。")
        return safe, warnings

    def validate_recommendation(self, recommendation: InterviewRecommendation) -> InterviewRecommendation:
        questions, warnings = self.filter_questions(recommendation.recommended_questions)
        limitations = list(recommendation.limitations)
        limitations.extend(warnings)
        return recommendation.model_copy(update={"recommended_questions": questions, "limitations": limitations})
