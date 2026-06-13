from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AchievementCandidate(BaseModel):
    candidate_event_id: str
    source_section: str = "unknown"
    source_sentence: str
    isolated_clause: str
    detected_numeric_expressions: list[str] = Field(default_factory=list)
    linked_career_context: Optional[str] = None
    detection_reason: str
    period_months: Optional[int] = None


class RawAchievementEvent(BaseModel):
    raw_achievement_id: str
    raw_metric_name: str
    raw_achievement_text: str
    metric_value: Optional[float] = None
    metric_value_upper: Optional[float] = None
    unit: Optional[str] = None
    period_months: Optional[int] = None
    approximate: bool = False
    lower_bound: bool = False
    evidence_quote: str
    model_config = ConfigDict(extra="forbid")
