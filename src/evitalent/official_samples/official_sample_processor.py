from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from evitalent.extraction.grounding_validator import GroundingValidator
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline, HybridExtractionResult
from evitalent.extraction.llm_client import LLMClient
from evitalent.extraction.llm_single_event_extractor import LLMSingleEventExtractor
from evitalent.extraction.llm_structure_extractor import LLMStructureExtractor
from evitalent.official_samples.private_manifest import OfficialDocumentRecord, write_json
from evitalent.official_samples.settings import OfficialSampleSettings
from evitalent.parser.docx_parser import DocxDocumentParser
from evitalent.privacy.pii_detector import detect_pii
from evitalent.privacy.redactor import RedactionResult, redact_text
from evitalent.scoring.ranker import rank_candidates


HIGH_RISK_PII = {
    "person_name",
    "phone",
    "email",
    "id_card",
    "birth_date",
    "marital_status",
    "family_status",
    "native_place",
    "detailed_address",
    "salary_current",
    "salary_expected",
}


@dataclass
class SafeTextCheck:
    passed: bool
    detected_types: list[str] = field(default_factory=list)
    sensitive_leakage_count: int = 0


@dataclass
class RedactionPilotResult:
    document_id: str
    domain: str
    parse_status: str
    redaction_status: str
    detected_pii_type_counts: dict[str, int]
    safety_passed: bool
    warning_count: int
    redacted_output_path: str


class CountingLLMClient(LLMClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.request_count = 0
        self.total_request_seconds = 0.0

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        started = perf_counter()
        try:
            return super().generate_json(system_prompt, user_prompt)
        finally:
            self.request_count += 1
            self.total_request_seconds += perf_counter() - started


class OfficialSampleProcessor:
    def __init__(self, settings: OfficialSampleSettings, parser: DocxDocumentParser | None = None) -> None:
        self.settings = settings
        self.parser = parser or DocxDocumentParser()

    def private_path(self, record: OfficialDocumentRecord) -> Path:
        path = (self.settings.resume_input_root / record.private_relative_path).resolve()
        root = self.settings.resume_input_root.resolve()
        if root not in path.parents and path != root:
            raise ValueError("Official sample path must stay inside the private input root.")
        return path

    def parse_and_redact(self, record: OfficialDocumentRecord, output_root: Path | None = None) -> RedactionPilotResult:
        parsed = self.parser.parse(self.private_path(record))
        redaction = redact_text(parsed.cleaned_text)
        check = self.check_redacted_text(redaction.redacted_text)
        out_root = output_root or self.settings.redacted_pilot_dir
        output_path = out_root / record.folder_domain / f"{record.document_id}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(redaction.redacted_text, encoding="utf-8")
        return RedactionPilotResult(
            document_id=record.document_id,
            domain=record.folder_domain,
            parse_status=parsed.parse_status,
            redaction_status="passed" if check.passed else "failed_safety",
            detected_pii_type_counts=self._summary(redaction),
            safety_passed=check.passed,
            warning_count=len(parsed.warnings) + check.sensitive_leakage_count,
            redacted_output_path=str(output_path.relative_to(self.settings.private_data_root)),
        )

    def run_local_ollama_extraction(self, document_id: str, domain: str, redacted_text: str, client: CountingLLMClient | None = None) -> dict:
        if self.settings.allow_mock_fallback:
            raise ValueError("Official samples must not allow mock fallback.")
        check = self.check_redacted_text(redacted_text)
        if not check.passed:
            raise ValueError("Redacted text failed safety check; LLM extraction blocked.")
        client = client or CountingLLMClient(
            provider="local_ollama",
            base_url="http://127.0.0.1:11434",
            api_key="ollama",
            model="evitalent-extractor:7b",
            temperature=0,
            timeout_seconds=600,
            max_retries=1,
            seed=9,
        )
        if client.provider == "mock":
            raise ValueError("Official samples cannot be processed with mock LLM provider.")
        started = perf_counter()
        structure_extractor = LLMStructureExtractor(client=client, use_llm=True)
        single_event_extractor = LLMSingleEventExtractor(client=client, use_llm=True)
        pipeline = HybridExtractionPipeline(
            structure_extractor=structure_extractor,
            single_event_extractor=single_event_extractor,
            grounding_validator=GroundingValidator(),
        )
        result: HybridExtractionResult = pipeline.extract(redacted_text, document_id=document_id, candidate_id=document_id)
        detected_domains = result.candidate_extraction.candidate_profile.target_domains
        status = "matched" if domain in detected_domains else "mismatch_needs_review"
        ranking = rank_candidates([result.candidate_extraction], domain=domain, ranking_id=f"{document_id}_{domain}_pilot")
        ranked = ranking.candidates[0]
        summary = result.summary
        eligible = bool(summary["eligible_for_scoring"] and check.passed)
        return {
            "document_id": document_id,
            "folder_domain": domain,
            "detected_domains": detected_domains,
            "domain_match_status": status,
            "career_record_count": len(result.candidate_extraction.career_records),
            "achievement_candidate_count": summary["achievement_candidate_count"],
            "raw_event_count": summary["raw_event_count"],
            "normalized_event_count": summary["normalized_event_count"],
            "grounded_event_count": summary["grounded_event_count"],
            "needs_review_count": summary["needs_review_event_count"],
            "schema_passed": True,
            "safety_passed": check.passed,
            "eligible_for_scoring": eligible,
            "bcs": ranked.bcs,
            "eci": ranked.eci,
            "penalty": ranked.penalty,
            "rank_score": ranked.rank_score,
            "actual_llm_request_count": client.request_count,
            "inference_seconds": round(perf_counter() - started, 4),
            "candidate_extraction": result.candidate_extraction.model_dump(mode="json"),
        }

    @staticmethod
    def check_redacted_text(text: str) -> SafeTextCheck:
        leaks = []
        for item in detect_pii(text):
            if item.pii_type not in HIGH_RISK_PII:
                continue
            # Mask tokens are bracketed. They are allowed; raw detected values are not.
            if item.original_text.startswith("[") or "已脱敏" in item.original_text or "宸茶劚" in item.original_text:
                continue
            leaks.append(item.pii_type)
        return SafeTextCheck(passed=not leaks, detected_types=sorted(set(leaks)), sensitive_leakage_count=len(leaks))

    @staticmethod
    def _summary(redaction: RedactionResult) -> dict[str, int]:
        return dict(sorted(redaction.redaction_summary.items()))


def save_redaction_pilot_outputs(settings: OfficialSampleSettings, rows: list[RedactionPilotResult]) -> None:
    private_payload = {"documents": [row.__dict__ for row in rows]}
    safe_payload = {"documents": [row.__dict__ for row in rows]}
    write_json(settings.redaction_pilot_private_path, private_payload)
    write_json(settings.redaction_pilot_safe_summary_path, safe_payload)
