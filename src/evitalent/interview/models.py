from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


FitLevel = Literal["high", "medium", "low"]
Priority = Literal["high", "medium", "low"]


class HighFitCondition(BaseModel):
    condition_id: str
    label: str
    fit_level: FitLevel
    basis: str
    related_event_type: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class InterviewFocusArea(BaseModel):
    focus_id: str
    focus_name: str
    focus_type: Literal["strength_validation", "depth_probe", "scale_context", "transferability", "risk_check"]
    reason: str
    related_evidence_ids: list[str] = Field(default_factory=list)
    priority: Priority


class RecommendedQuestion(BaseModel):
    question_id: str
    question_type: Literal["behavioral", "situational", "evidence_verification", "technical_depth", "management_probe", "risk_probe"]
    question: str
    why_ask: str
    evidence_basis: str
    follow_up_probe: str
    expected_good_answer: str
    red_flags: list[str] = Field(default_factory=list)
    related_competency: str
    suggested_score_dimension: str


class RiskVerificationItem(BaseModel):
    risk_id: str
    risk_type: str
    description: str
    suggested_probe: str
    related_risk_flag_ids: list[str] = Field(default_factory=list)


class InterviewScorecardDimension(BaseModel):
    dimension: str
    weight: float = Field(ge=0, le=1)
    observation_points: list[str] = Field(default_factory=list)


class InterviewRecommendation(BaseModel):
    candidate_id: str
    target_domain: str
    job_title: str
    fit_summary: str
    high_fit_conditions: list[HighFitCondition] = Field(default_factory=list)
    interview_focus_areas: list[InterviewFocusArea] = Field(default_factory=list)
    recommended_questions: list[RecommendedQuestion] = Field(default_factory=list)
    risk_verification_items: list[RiskVerificationItem] = Field(default_factory=list)
    suggested_interview_scorecard: list[InterviewScorecardDimension] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    version: str = "interview_focus_v1"

    @property
    def safety_passed(self) -> bool:
        return not any("被移除" in item or "最终决策" in item for item in self.limitations)
