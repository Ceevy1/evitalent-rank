from __future__ import annotations

from typing import Any, Optional

from evitalent.interview.competency_matcher import CompetencyMatcher, _event_type, _get
from evitalent.interview.interview_focus_analyzer import InterviewFocusAnalyzer
from evitalent.interview.interview_safety_guard import InterviewSafetyGuard
from evitalent.interview.llm_question_generator import LLMQuestionGenerator
from evitalent.interview.models import (
    InterviewRecommendation,
    InterviewScorecardDimension,
    RecommendedQuestion,
    RiskVerificationItem,
)
from evitalent.interview.question_template_bank import QuestionTemplateBank


class InterviewRecommendationService:
    def __init__(
        self,
        matcher: Optional[CompetencyMatcher] = None,
        focus_analyzer: Optional[InterviewFocusAnalyzer] = None,
        template_bank: Optional[QuestionTemplateBank] = None,
        safety_guard: Optional[InterviewSafetyGuard] = None,
        llm_generator: Optional[LLMQuestionGenerator] = None,
    ) -> None:
        self.matcher = matcher or CompetencyMatcher()
        self.focus_analyzer = focus_analyzer or InterviewFocusAnalyzer()
        self.template_bank = template_bank or QuestionTemplateBank()
        self.safety_guard = safety_guard or InterviewSafetyGuard()
        self.llm_generator = llm_generator or LLMQuestionGenerator(enabled=False)

    def recommend(self, analysis: Any, jd_requirements: Optional[str] = None) -> InterviewRecommendation:
        candidate_id = str(_get(analysis, "candidate_id", None) or _get(analysis, "document_id", None) or _get(analysis, "候选人编号", "anonymous_candidate"))
        domain = str(_get(analysis, "target_domain", None) or _get(analysis, "domain", None) or _get(analysis, "folder_domain", "hr"))
        job_title = str(_get(analysis, "job_title", "") or _get(analysis, "岗位名称", "") or "目标岗位")
        conditions = self.matcher.match(analysis)
        focus_areas = self.focus_analyzer.analyze(conditions, analysis)
        questions = self._build_questions(domain, conditions, focus_areas, analysis)
        risk_items = self._build_risk_items(analysis)
        questions.extend(self._build_risk_questions(risk_items, len(questions)))
        min_questions = 8 if float(_get(analysis, "rank_score", 0) or 0) >= 70 else 5
        while len(questions) < min_questions:
            questions.append(self._generic_question(len(questions), conditions[0].label if conditions else "岗位匹配"))
        scorecard = self._scorecard(domain, conditions)
        limitations = [
            "面试重点推荐仅用于面试辅助，不构成录用或淘汰决定。",
            "推荐问题基于安全匿名结构化结果、已核验证据摘要和风险标签生成。",
        ]
        if not _get(analysis, "normalized_achievement_events", None) and not _get(analysis, "achievement_events", None):
            limitations.append("当前安全摘要中缺少完整成果事件，建议面试核验关键成果。")
        recommendation = InterviewRecommendation(
            candidate_id=candidate_id,
            target_domain=domain,
            job_title=job_title,
            fit_summary=self._fit_summary(conditions, risk_items),
            high_fit_conditions=conditions,
            interview_focus_areas=focus_areas,
            recommended_questions=questions[:10],
            risk_verification_items=risk_items,
            suggested_interview_scorecard=scorecard,
            limitations=limitations,
        )
        return self.safety_guard.validate_recommendation(recommendation)

    def _build_questions(self, domain: str, conditions: list, focus_areas: list, analysis: Any) -> list[RecommendedQuestion]:
        events = list(_get(analysis, "normalized_achievement_events", None) or _get(analysis, "achievement_events", []) or [])
        questions: list[RecommendedQuestion] = []
        for index, event in enumerate(events[:6]):
            event_type = _event_type(event)
            template = self.template_bank.get_template(domain, event_type)
            competency = next((condition.label for condition in conditions if condition.related_event_type == event_type), event_type or "岗位成果")
            question_text = template.question_template.format(competency=competency)
            evidence_id = str(_get(event, "evidence_id", "") or "")
            questions.append(
                RecommendedQuestion(
                    question_id=f"q_event_{index}",
                    question_type="evidence_verification",
                    question=self.llm_generator.rewrite(question_text, evidence_id),
                    why_ask="该问题用于验证结构化成果的真实性、个人贡献和业务口径。",
                    evidence_basis=evidence_id or "已核验结构化成果事件",
                    follow_up_probe=template.follow_up_template,
                    expected_good_answer=template.expected_good_answer_template,
                    red_flags=template.red_flags,
                    related_competency=str(competency),
                    suggested_score_dimension=template.score_dimension,
                )
            )
        for index, focus in enumerate(focus_areas[:4]):
            if len(questions) >= 8:
                break
            if focus.focus_type == "risk_check":
                continue
            questions.append(
                RecommendedQuestion(
                    question_id=f"q_focus_{index}",
                    question_type="behavioral" if focus.focus_type == "strength_validation" else "technical_depth",
                    question=f"请结合一个具体案例说明你如何体现“{focus.focus_name}”，并说明个人贡献和结果。",
                    why_ask=focus.reason,
                    evidence_basis="面试重点分析结果",
                    follow_up_probe="请进一步说明当时的约束条件、协作对象、数据口径和复盘结论。",
                    expected_good_answer="能清楚说明背景、目标、行动、个人贡献、结果证据和可迁移经验。",
                    red_flags=["只描述团队成绩", "无法说明个人动作", "不能解释结果口径"],
                    related_competency=focus.focus_name,
                    suggested_score_dimension="面试验证重点",
                )
            )
        return questions

    def _build_risk_items(self, analysis: Any) -> list[RiskVerificationItem]:
        risk_flags = list(_get(analysis, "risk_flags", []) or [])
        if not risk_flags and _get(analysis, "待核验事项"):
            risk_flags = [item.strip() for item in str(_get(analysis, "待核验事项")).split("、") if item.strip()]
        if float(_get(analysis, "eci", _get(analysis, "材料可信度", 100)) or 100) < 70:
            risk_flags.append("材料可信度偏低")
        return [
            RiskVerificationItem(
                risk_id=f"risk_{index}",
                risk_type=str(flag).split(" ")[0],
                description=str(flag),
                suggested_probe=f"请围绕“{flag}”说明事实依据、数据口径和可补充证明材料。",
                related_risk_flag_ids=[f"risk_flag_{index}"],
            )
            for index, flag in enumerate(risk_flags[:5])
        ]

    def _build_risk_questions(self, risk_items: list[RiskVerificationItem], offset: int) -> list[RecommendedQuestion]:
        questions = []
        for index, item in enumerate(risk_items[:3]):
            questions.append(
                RecommendedQuestion(
                    question_id=f"q_risk_{offset + index}",
                    question_type="risk_probe",
                    question=item.suggested_probe,
                    why_ask="该事项在简历分析结果中被标记为待核验，建议面试进一步确认。",
                    evidence_basis=item.description,
                    follow_up_probe="请说明是否有可复核的项目记录、业务报表或第三方证明。",
                    expected_good_answer="能明确说明事实来源、本人角色、时间范围和结果口径；若信息不足，应主动说明边界。",
                    red_flags=["回避核验问题", "数据口径模糊", "无法说明本人角色"],
                    related_competency=item.risk_type,
                    suggested_score_dimension="风险核验",
                )
            )
        return questions

    def _generic_question(self, index: int, competency: str) -> RecommendedQuestion:
        return RecommendedQuestion(
            question_id=f"q_generic_{index}",
            question_type="situational",
            question=f"如果进入当前岗位，你会如何在前三个月验证并发挥“{competency}”？",
            why_ask="当前安全证据有限，需要通过情境问题确认能力迁移性。",
            evidence_basis="安全摘要与岗位方向",
            follow_up_probe="请说明优先事项、协作对象、关键指标和风险预案。",
            expected_good_answer="能结合岗位目标提出清晰计划、衡量指标和风险控制方式。",
            red_flags=["计划空泛", "不能说明衡量指标", "忽视岗位资源约束"],
            related_competency=competency,
            suggested_score_dimension="迁移能力",
        )

    def _scorecard(self, domain: str, conditions: list) -> list[InterviewScorecardDimension]:
        labels = [condition.label for condition in conditions[:3]] or ["岗位匹配", "成果真实性", "风险核验"]
        dimensions = [
            InterviewScorecardDimension(dimension=labels[0], weight=0.3, observation_points=["事实是否清晰", "个人贡献是否明确", "可迁移性是否成立"]),
            InterviewScorecardDimension(dimension=labels[1] if len(labels) > 1 else "成果真实性", weight=0.25, observation_points=["结果口径", "证据链", "复盘能力"]),
            InterviewScorecardDimension(dimension="岗位迁移能力", weight=0.25, observation_points=["目标理解", "资源适配", "落地计划"]),
            InterviewScorecardDimension(dimension="风险核验", weight=0.2, observation_points=["待核验事项回应", "边界意识", "补充材料可获得性"]),
        ]
        return dimensions

    def _fit_summary(self, conditions: list, risk_items: list[RiskVerificationItem]) -> str:
        if not conditions:
            return "当前安全摘要中的岗位契合证据有限，建议面试核验关键经历与成果。"
        top = "、".join(condition.label for condition in conditions[:3])
        risk_text = f"；同时有 {len(risk_items)} 项待核验事项需要面试确认" if risk_items else ""
        return f"候选人与目标岗位的主要契合点包括：{top}{risk_text}。"
