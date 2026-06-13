from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


StandardDirection = Literal["increase_by", "decrease_by", "achieved_level", "achieved_amount", "maintained", "unknown"]


class NormalizedAchievementEvent(BaseModel):
    achievement_id: str
    raw_achievement_id: str
    raw_achievement_text: str
    raw_metric_name: str
    normalized_metric_name: str
    metric_value: Optional[float] = None
    metric_value_upper: Optional[float] = None
    unit: Optional[str] = None
    event_type: str
    direction: StandardDirection
    period_months: Optional[int] = None
    approximate: bool = False
    lower_bound: bool = False
    evidence_quote: str
    evidence_id: str
    normalization_rule_id: str
    normalization_status: Literal["normalized", "needs_review"] = "normalized"
    eligible_for_core_achievement_score: bool = True
    grounding_status: Literal["passed", "failed"] = "passed"
    grounding_errors: list[str] = Field(default_factory=list)
