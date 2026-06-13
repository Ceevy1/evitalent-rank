from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from evitalent.privacy.pii_detector import detect_pii
from evitalent.settings import PROJECT_ROOT


class PromptSecurityError(ValueError):
    pass


@dataclass(frozen=True)
class RedactedResumeInput:
    document_id: str
    redacted_text: str
    redaction_completed: bool
    target_domain: str | None = None
    candidate_id_hint: str | None = None


class PromptBuilder:
    def __init__(
        self,
        system_prompt_path: str | Path | None = None,
        user_template_path: str | Path | None = None,
    ) -> None:
        self.system_prompt_path = Path(system_prompt_path) if system_prompt_path else PROJECT_ROOT / "prompts" / "resume_extraction_system_v1.txt"
        self.user_template_path = Path(user_template_path) if user_template_path else PROJECT_ROOT / "prompts" / "resume_extraction_user_template_v1.txt"

    def build(self, resume_input: RedactedResumeInput) -> tuple[str, str]:
        self._assert_safe_input(resume_input)
        system_prompt = self.system_prompt_path.read_text(encoding="utf-8")
        user_template = self.user_template_path.read_text(encoding="utf-8")
        schema_brief = {
            "required_top_level_fields": [
                "schema_version",
                "document_id",
                "candidate_id",
                "parse_metadata",
                "sensitive_information",
                "candidate_profile",
                "education_records",
                "career_records",
                "project_records",
                "achievement_events",
                "domain_assessment_inputs",
                "evidence_items",
                "quality_flags",
                "llm_metadata",
            ],
            "achievement_event_rules": "A/B 可进入成果评分，C 仅用于能力标签，D 不进入主评分。",
            "privacy_rule": "sensitive_information.masked_for_scoring 必须为 true；敏感字段不得进入评分输入。",
        }
        user_prompt = user_template.format(
            document_id=resume_input.document_id,
            candidate_id=resume_input.candidate_id_hint or f"candidate_{resume_input.document_id}",
            target_domain=resume_input.target_domain or "auto",
            schema_brief=json.dumps(schema_brief, ensure_ascii=False, indent=2),
            redacted_text=resume_input.redacted_text,
        )
        return system_prompt, user_prompt

    @staticmethod
    def _assert_safe_input(resume_input: RedactedResumeInput) -> None:
        if not resume_input.redaction_completed:
            raise PromptSecurityError("未完成脱敏，禁止构造 LLM 请求。")
        if not resume_input.redacted_text.strip():
            raise PromptSecurityError("脱敏文本为空，禁止构造 LLM 请求。")
        high_risk = {"phone", "email", "id_card", "salary_current", "salary_expected"}
        findings = [
            item
            for item in detect_pii(resume_input.redacted_text)
            if item.pii_type in high_risk and "已脱敏" not in item.original_text
        ]
        if findings:
            types = sorted({item.pii_type for item in findings})
            raise PromptSecurityError(f"脱敏文本仍疑似包含敏感字段：{', '.join(types)}")
