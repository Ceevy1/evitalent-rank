from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AuditIssue(BaseModel):
    issue_type: str
    severity: Literal["info", "warning", "critical"] = "info"
    description: str
    candidate_id: Optional[str] = None
    related_evidence_ids: list[str] = Field(default_factory=list)


class TimelineAuditResult(BaseModel):
    issue_count: int
    critical_issue_count: int
    timeline_consistency_score: float
    detected_issues: list[AuditIssue] = Field(default_factory=list)
    penalty_recommendation: float = 0.0
    related_evidence_ids: list[str] = Field(default_factory=list)


class FairnessAuditResult(BaseModel):
    fairness_audit_status: Literal["passed", "warning", "failed"]
    sensitive_field_isolation_passed: bool
    counterfactual_invariance_passed: bool
    candidate_score_shift: dict[str, float] = Field(default_factory=dict)
    candidate_rank_shift: dict[str, int] = Field(default_factory=dict)
    mean_score_shift: float = 0.0
    max_score_shift: float = 0.0
    mean_rank_shift: float = 0.0
    max_rank_shift: int = 0
    detected_issues: list[AuditIssue] = Field(default_factory=list)


class RobustnessAuditResult(BaseModel):
    robustness_audit_status: Literal["passed", "warning", "failed"]
    top_k: int = 3
    comparisons: dict[str, dict[str, Any]] = Field(default_factory=dict)
    rankings_by_version: dict[str, list[str]] = Field(default_factory=dict)
    score_stability: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class OverallConclusion(BaseModel):
    overall_audit_status: Literal["passed", "warning", "failed"]
    conclusion_summary: list[str]
    critical_issue_count: int = 0


class AuditResult(BaseModel):
    audit_id: str
    ranking_id: str
    domain: str
    audit_version: str = "stage7_v1"
    generated_at: str
    timeline_audit: dict[str, Any] = Field(default_factory=dict)
    fairness_audit: dict[str, Any] = Field(default_factory=dict)
    robustness_audit: dict[str, Any] = Field(default_factory=dict)
    overall_conclusion: OverallConclusion
    limitations: list[str] = Field(default_factory=list)
