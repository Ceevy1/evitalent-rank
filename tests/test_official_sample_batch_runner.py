from __future__ import annotations

from dataclasses import dataclass

from evitalent.official_samples.batch_extraction_runner import OfficialBatchExtractionRunner
from evitalent.official_samples.batch_state_store import COMPLETED_ELIGIBLE, FAILED_REDACTION
from evitalent.official_samples.inventory_service import OfficialInventoryService
from evitalent.official_samples.official_sample_processor import RedactionPilotResult
from evitalent.official_samples.private_manifest import write_json
from evitalent.official_samples.redaction_review_gate import confirm_redaction_review
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import DOMAINS, make_private_tree


@dataclass
class FakeProcessor:
    settings: object
    fail_domain: str = "sales"

    def parse_and_redact(self, record, output_root=None):
        path = output_root / record.folder_domain / f"{record.document_id}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("招聘完成18人", encoding="utf-8")
        return RedactionPilotResult(
            document_id=record.document_id,
            domain=record.folder_domain,
            parse_status="success",
            redaction_status="failed_safety" if record.folder_domain == self.fail_domain else "passed",
            detected_pii_type_counts={},
            safety_passed=record.folder_domain != self.fail_domain,
            warning_count=0,
            redacted_output_path=str(path.relative_to(self.settings.private_data_root)),
        )

    def run_local_ollama_extraction(self, document_id, domain, redacted_text):
        return {
            "document_id": document_id,
            "folder_domain": domain,
            "eligible_for_scoring": True,
            "actual_llm_request_count": 2,
            "inference_seconds": 1.0,
            "candidate_extraction": {},
        }


def test_batch_runner_checkpoint_and_safe_summary_without_sensitive_values(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    manifest = OfficialInventoryService(settings).scan()

    # Minimal gate prerequisites.
    rows = []
    for domain in DOMAINS:
        doc_id = f"{domain}_abc"
        rel = f"redacted/resumes/pilot/{domain}/{doc_id}.txt"
        path = settings.private_data_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("已脱敏文本", encoding="utf-8")
        rows.append({"document_id": doc_id, "domain": domain, "safety_passed": True, "redacted_output_path": rel})
    write_json(settings.redaction_pilot_safe_summary_path, {"documents": rows})
    confirm_redaction_review(settings)
    write_json(settings.llm_pilot_safe_summary_path, {"documents": [{"domain": d, "safety_passed": True} for d in DOMAINS]})

    summary = OfficialBatchExtractionRunner(settings, processor=FakeProcessor(settings)).run(manifest)
    state = (settings.batch_state_path).read_text(encoding="utf-8")
    assert COMPLETED_ELIGIBLE in state
    assert FAILED_REDACTION in state
    assert "13900001111" not in str(summary)
    assert "sample.docx" not in str(summary)
