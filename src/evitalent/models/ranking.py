from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field


class CandidateFeatures(BaseModel):
    candidate_id: str
    display_id: str
    domain: str
    axis_scores: dict[str, float]
    evidence_ids_by_axis: dict[str, list[str]] = Field(default_factory=dict)
    metrics: dict[str, Optional[Union[float, int, str, bool]]] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)


class StrengthItem(BaseModel):
    axis: str
    label: str
    score: float
    evidence_ids: list[str] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    evidence_count: int
    scoring_evidence_count: int
    achievement_event_count: int
    quantified_achievement_count: int


class CandidateRankingResult(BaseModel):
    rank: int
    candidate_id: str
    bcs: float
    eci: float
    penalty: float
    rank_score: float
    axis_scores: dict[str, float]
    computed_features: dict = Field(default_factory=dict)
    top_strengths: list[StrengthItem] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    evidence_summary: EvidenceSummary

    # Backward-compatible fields used by earlier scripts.
    display_id: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)


class RankingResult(BaseModel):
    ranking_id: str
    domain: str
    domain_label: str
    generated_at: str
    ranking_method_version: str = "stage4_v1"
    candidates: list[CandidateRankingResult]
    insufficient_candidates_for_ranking: bool = False

    schema_version: str = "1.0.0"

    @property
    def created_at(self) -> str:
        return self.generated_at

    @property
    def results(self) -> list[CandidateRankingResult]:
        return self.candidates
