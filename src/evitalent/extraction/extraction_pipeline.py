from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evitalent.extraction.evidence_linker import check_evidence_links
from evitalent.extraction.schema_validator import SchemaValidationError, SchemaValidator
from evitalent.models.extraction import CandidateExtraction
from evitalent.privacy.pii_detector import detect_pii


class ExtractionPipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractionPipelineResult:
    candidate: CandidateExtraction | None
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected_due_to_sensitive_content: bool = False


class ExtractionPipeline:
    def __init__(self, schema_validator: SchemaValidator | None = None) -> None:
        self.schema_validator = schema_validator or SchemaValidator()

    def validate_payload(self, payload: dict[str, Any], save_path: Path | None = None) -> ExtractionPipelineResult:
        errors: list[str] = []
        warnings: list[str] = []
        try:
            self.schema_validator.validate_or_raise(payload)
            candidate = CandidateExtraction.model_validate(payload)
        except SchemaValidationError as exc:
            return ExtractionPipelineResult(None, False, [f"JSON Schema 校验失败：{exc}"])
        except ValidationError as exc:
            return ExtractionPipelineResult(None, False, [f"Pydantic 校验失败：{exc}"])

        link_result = check_evidence_links(candidate)
        if not link_result["passed"]:
            errors.append(f"证据引用校验失败：{link_result}")
        warnings.extend(link_result.get("warnings", []))

        sensitive_errors = self._check_sensitive_leakage(candidate, payload)
        if sensitive_errors:
            errors.extend(sensitive_errors)
            return ExtractionPipelineResult(candidate, False, errors, warnings, rejected_due_to_sensitive_content=True)
        if errors:
            return ExtractionPipelineResult(candidate, False, errors, warnings)

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")
        return ExtractionPipelineResult(candidate, True, warnings=warnings)

    def validate_or_raise(self, payload: dict[str, Any], save_path: Path | None = None) -> CandidateExtraction:
        result = self.validate_payload(payload, save_path)
        if not result.passed or result.candidate is None:
            raise ExtractionPipelineError("; ".join(result.errors))
        return result.candidate

    @staticmethod
    def _check_sensitive_leakage(candidate: CandidateExtraction, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if candidate.sensitive_information.masked_for_scoring is not True:
            errors.append("sensitive_information.masked_for_scoring 必须为 true。")

        scoring_blob = json.dumps(payload.get("domain_assessment_inputs", {}), ensure_ascii=False).lower()
        forbidden_keys = ["gender", "birth_year", "marital", "salary", "薪资", "婚姻", "性别", "出生"]
        if any(key in scoring_blob for key in forbidden_keys):
            errors.append("domain_assessment_inputs 中疑似包含敏感字段。")

        quote_blob = "\n".join(item.quote for item in candidate.evidence_items)
        high_risk = {"phone", "email", "id_card", "salary_current", "salary_expected"}
        leaked = sorted(
            {
                item.pii_type
                for item in detect_pii(quote_blob)
                if item.pii_type in high_risk and "已脱敏" not in item.original_text
            }
        )
        if leaked:
            errors.append(f"evidence quote 中疑似包含敏感字段：{', '.join(leaked)}。")
        return errors
