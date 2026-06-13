from __future__ import annotations

from pathlib import Path
from typing import Any

from evitalent.official_samples.batch_state_store import (
    COMPLETED_ELIGIBLE,
    COMPLETED_NEEDS_REVIEW,
    FAILED_MODEL_REQUEST,
    FAILED_REDACTION,
    FAILED_SAFETY,
    PROCESSING,
    BatchStateStore,
)
from evitalent.official_samples.official_sample_processor import OfficialSampleProcessor
from evitalent.official_samples.private_manifest import OfficialDocumentRecord, OfficialManifest, write_json
from evitalent.official_samples.redaction_review_gate import assert_llm_pilot_allowed
from evitalent.official_samples.settings import OfficialSampleSettings


class OfficialBatchExtractionRunner:
    def __init__(self, settings: OfficialSampleSettings, processor: OfficialSampleProcessor | None = None) -> None:
        self.settings = settings
        self.processor = processor or OfficialSampleProcessor(settings)
        self.state = BatchStateStore(settings.batch_state_path)

    def run(self, manifest: OfficialManifest, resume: bool = False) -> dict[str, Any]:
        assert_llm_pilot_allowed(self.settings)
        if not self.settings.llm_pilot_safe_summary_path.exists():
            raise RuntimeError("LLM pilot must complete before batch extraction.")
        records = sorted(
            [item for item in manifest.documents if item.parser_readable and not item.is_duplicate],
            key=lambda item: (self.settings.domains.index(item.folder_domain), item.document_id),
        )
        self.state.initialize([record.__dict__ for record in records], resume=resume)
        total_requests = 0
        total_seconds = 0.0
        leakage = 0
        for record in records:
            if resume and self.state.is_final(record.document_id):
                continue
            self.state.mark(record.document_id, PROCESSING)
            try:
                redaction = self.processor.parse_and_redact(record, output_root=self.settings.redacted_batch_dir)
                if not redaction.safety_passed:
                    leakage += 1
                    self.state.mark(record.document_id, FAILED_REDACTION, domain=record.folder_domain)
                    continue
                text_path = self.settings.private_data_root / redaction.redacted_output_path
                result = self.processor.run_local_ollama_extraction(record.document_id, record.folder_domain, text_path.read_text(encoding="utf-8"))
                total_requests += int(result["actual_llm_request_count"])
                total_seconds += float(result["inference_seconds"])
                result_path = self._result_path(record)
                write_json(result_path, result)
                status = COMPLETED_ELIGIBLE if result.get("eligible_for_scoring") else COMPLETED_NEEDS_REVIEW
                self.state.mark(record.document_id, status, domain=record.folder_domain, result_path=str(result_path))
            except ValueError as exc:
                status = FAILED_SAFETY if "safety" in str(exc).lower() else FAILED_MODEL_REQUEST
                self.state.mark(record.document_id, status, domain=record.folder_domain, error_type=type(exc).__name__)
            except Exception as exc:
                self.state.mark(record.document_id, FAILED_MODEL_REQUEST, domain=record.folder_domain, error_type=type(exc).__name__)
        summary = self.safe_summary(total_requests, total_seconds, leakage)
        write_json(self.settings.batch_output_dir / "safe_processing_summary.json", summary)
        self._write_failed_documents()
        return summary

    def _result_path(self, record: OfficialDocumentRecord) -> Path:
        return self.settings.batch_output_dir / "extraction_results_private" / record.folder_domain / f"{record.document_id}.json"

    def safe_summary(self, total_requests: int, total_seconds: float, leakage: int) -> list[dict]:
        state = self.state.load()
        rows: list[dict] = []
        docs = state.get("documents", {})
        for domain in self.settings.domains:
            domain_docs = [item for item in docs.values() if item.get("domain") == domain]
            rows.append(
                {
                    "domain": domain,
                    "total_documents": len(domain_docs),
                    "processed_documents": sum(1 for item in domain_docs if item.get("status") != "pending"),
                    "eligible_documents": sum(1 for item in domain_docs if item.get("status") == COMPLETED_ELIGIBLE),
                    "needs_review_documents": sum(1 for item in domain_docs if item.get("status") == COMPLETED_NEEDS_REVIEW),
                    "failed_documents": sum(1 for item in domain_docs if str(item.get("status", "")).startswith("failed")),
                    "total_llm_requests": total_requests,
                    "total_inference_seconds": round(total_seconds, 4),
                    "average_document_inference_seconds": round(total_seconds / max(1, sum(1 for item in docs.values() if item.get("status") != "pending")), 4),
                    "sensitive_leakage_count": leakage,
                }
            )
        return rows

    def _write_failed_documents(self) -> None:
        state = self.state.load()
        failed = [item for item in state.get("documents", {}).values() if str(item.get("status", "")).startswith("failed")]
        write_json(self.settings.batch_output_dir / "failed_documents_private.json", {"documents": failed})
