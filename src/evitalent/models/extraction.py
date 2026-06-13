from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AchievementEventType(str, Enum):
    revenue_growth = "revenue_growth"
    gmv_growth = "gmv_growth"
    roi_improvement = "roi_improvement"
    conversion_improvement = "conversion_improvement"
    cost_reduction = "cost_reduction"
    efficiency_improvement = "efficiency_improvement"
    loss_reduction = "loss_reduction"
    quality_improvement = "quality_improvement"
    recruitment_delivery = "recruitment_delivery"
    recruitment_completion_rate = "recruitment_completion_rate"
    retention_improvement = "retention_improvement"
    organization_transformation = "organization_transformation"
    product_launch = "product_launch"
    automation_upgrade = "automation_upgrade"
    promotion_award = "promotion_award"
    patent_publication = "patent_publication"
    technology_transfer = "technology_transfer"
    collection_performance = "collection_performance"
    channel_expansion = "channel_expansion"
    other = "other"


class EvidenceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ParseMetadata(BaseModel):
    source_type: str
    parsed_at: str
    parser_version: str = "v1"
    redacted_text_path: Optional[str] = None
    source_filename: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class SensitiveInformation(BaseModel):
    name_detected: bool
    gender: Optional[str] = None
    birth_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    marital_status: Optional[str] = None
    salary_current: Optional[str] = None
    salary_expected: Optional[str] = None
    location: Optional[str] = None
    masked_for_scoring: Literal[True]

    # Backward-compatible fields/properties used by earlier tests or modules.
    name_present: bool = False
    birth_date_present: bool = False
    age_present: bool = False
    marital_status_present: bool = False
    family_status_present: bool = False
    native_place_present: bool = False
    current_salary_present: bool = False
    expected_salary_present: bool = False
    redaction_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_legacy_flags(self) -> "SensitiveInformation":
        self.name_present = self.name_detected
        self.birth_date_present = self.birth_year is not None
        self.marital_status_present = self.marital_status is not None
        self.native_place_present = self.location is not None
        self.current_salary_present = self.salary_current is not None
        self.expected_salary_present = self.salary_expected is not None
        return self


class TargetDomainCandidate(BaseModel):
    domain: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class CandidateProfile(BaseModel):
    display_id: str
    target_domain_candidates: list[TargetDomainCandidate]
    summary: str = ""
    target_domains: list[str] = Field(default_factory=list)
    highest_degree: Optional[str] = None
    major: Optional[str] = None
    total_years_experience: Optional[float] = None
    current_level: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _sync_target_domains(self) -> "CandidateProfile":
        if not self.target_domains:
            self.target_domains = [item.domain for item in self.target_domain_candidates]
        return self


class EducationRecord(BaseModel):
    school: str
    degree: str
    major: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    evidence_id: str = Field(min_length=1)
    model_config = ConfigDict(extra="allow")


class CareerRecord(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str
    domain_tags: list[str] = Field(default_factory=list)
    management_headcount: Optional[int] = Field(default=None, ge=0)
    platform_evidence: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list, min_length=1)
    evidence_id: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _sync_evidence_id(self) -> "CareerRecord":
        if not self.evidence_id and self.evidence_ids:
            self.evidence_id = self.evidence_ids[0]
        return self


class ProjectRecord(BaseModel):
    project_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str
    domain_tags: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list, min_length=1)
    evidence_id: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _sync_evidence_id(self) -> "ProjectRecord":
        if not self.evidence_id and self.evidence_ids:
            self.evidence_id = self.evidence_ids[0]
        return self


class AchievementEvent(BaseModel):
    achievement_id: str = Field(min_length=1)
    event_type: AchievementEventType
    metric_name: str
    metric_value: Optional[float] = None
    metric_value_upper: Optional[float] = None
    unit: Optional[str] = None
    direction: Literal[
        "increase_by",
        "decrease_by",
        "achieved_level",
        "achieved_amount",
        "maintained",
        "unknown",
        "increase",
        "decrease",
        "maintain",
        "launch",
        "other",
    ]
    period_months: Optional[int] = Field(default=None, ge=0)
    approximate: bool = False
    lower_bound: bool = False
    candidate_contribution: str
    evidence_grade: EvidenceGrade
    evidence_id: str = Field(min_length=1)
    model_config = ConfigDict(extra="allow")


class DomainAssessmentInput(BaseModel):
    domain: str
    matched_tags: list[str] = Field(default_factory=list)
    competency_tags: list[str] = Field(default_factory=list)
    collaboration_tags: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    model_config = ConfigDict(extra="allow")


class EvidenceItem(BaseModel):
    evidence_id: str = Field(min_length=1)
    section: str
    quote: str = Field(min_length=1)
    fact_type: str
    used_for_scoring: bool
    page_number: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    model_config = ConfigDict(extra="allow")

    @property
    def source_section(self) -> str:
        return self.section


class QualityFlag(BaseModel):
    flag_type: str
    severity: Literal["info", "warning", "error"] = "info"
    description: str
    related_evidence_ids: list[str] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")

    @property
    def message(self) -> str:
        return self.description

    @property
    def evidence_id(self) -> Optional[str]:
        return self.related_evidence_ids[0] if self.related_evidence_ids else None


class LLMMetadata(BaseModel):
    provider: str
    model_name: str
    temperature: float = 0.0
    extracted_at: Optional[str] = None
    mode: str = "mock"
    model: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _sync_legacy_names(self) -> "LLMMetadata":
        self.mode = self.provider
        self.model = self.model_name
        return self


class CandidateExtraction(BaseModel):
    schema_version: str
    document_id: str
    candidate_id: str
    parse_metadata: ParseMetadata
    sensitive_information: SensitiveInformation
    candidate_profile: CandidateProfile
    education_records: list[EducationRecord] = Field(min_length=1)
    career_records: list[CareerRecord] = Field(min_length=2)
    project_records: list[ProjectRecord] = Field(min_length=1)
    achievement_events: list[AchievementEvent] = Field(min_length=1)
    domain_assessment_inputs: dict[str, DomainAssessmentInput]
    evidence_items: list[EvidenceItem] = Field(min_length=3)
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    llm_metadata: LLMMetadata
    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CandidateExtraction":
        return cls.model_validate(payload)

    @field_validator("domain_assessment_inputs")
    @classmethod
    def _has_domain_assessment(cls, value: dict[str, DomainAssessmentInput]) -> dict[str, DomainAssessmentInput]:
        if not value:
            raise ValueError("domain_assessment_inputs must contain at least one domain")
        return value

    @property
    def evidence_ids(self) -> set[str]:
        return {item.evidence_id for item in self.evidence_items}
