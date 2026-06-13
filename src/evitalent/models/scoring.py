from __future__ import annotations

from pydantic import BaseModel, Field


class AxisScoreResult(BaseModel):
    candidate_id: str
    domain: str
    axis_scores: dict[str, float]
    evidence_ids_by_axis: dict[str, list[str]] = Field(default_factory=dict)
    computed_features: dict = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)


class EvidenceScoreResult(BaseModel):
    eci: float
    parts: dict[str, float]
    warnings: list[str] = Field(default_factory=list)


class PenaltyResult(BaseModel):
    penalty: float
    flags: list[str] = Field(default_factory=list)
