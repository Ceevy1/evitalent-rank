from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    mode: str


class RankingRequest(BaseModel):
    domain: str = "hr"
    candidate_ids: Optional[list[str]] = None
    mode: str = "mock"


class ExtractionRequest(BaseModel):
    mode: str = "mock"


class ExtractionResponse(BaseModel):
    extraction_status: str
    candidate_id: str
    detected_domains: list[str] = Field(default_factory=list)
    career_count: int = 0
    achievement_count: int = 0
    evidence_count: int = 0
    quality_flags: list[str] = Field(default_factory=list)
    eligible_for_scoring: bool = False


class TimelineAuditRequest(BaseModel):
    candidate_ids: Optional[list[str]] = None
    domain: str = "hr"


class FairnessAuditRequest(BaseModel):
    ranking_id: str
    audit_mode: str = "deterministic_counterfactual"


class RobustnessAuditRequest(BaseModel):
    ranking_id: str
    audit_mode: str = "mock_equivalent_versions"
    top_k: int = 3


class UploadResponse(BaseModel):
    document_id: str
    source_filename: str
    file_type: str
    parse_status: str
    parse_url: str


class ParseResponse(BaseModel):
    document_id: str
    parse_status: str
    redacted_preview: str
    detected_pii_types: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ManualReviewRequest(BaseModel):
    document_id: str
    domain: str
    source_status: str
    decision: str
    reviewer: str = "人工审核员"
    note: str = ""
