import copy
import json
from pathlib import Path

from evitalent.extraction.extraction_pipeline import ExtractionPipeline
from evitalent.settings import PROJECT_ROOT


def _payload():
    return json.loads((PROJECT_ROOT / "data" / "fixtures" / "extracted" / "demo_hr_001.json").read_text(encoding="utf-8"))


def test_pipeline_accepts_valid_model_json_and_saves(tmp_path):
    payload = _payload()
    payload["document_id"] = "doc_llm_valid"
    payload["candidate_id"] = "candidate_llm_valid"
    path = tmp_path / "candidate_llm_valid.json"
    result = ExtractionPipeline().validate_payload(payload, save_path=path)
    assert result.passed is True
    assert path.exists()
    assert result.candidate.candidate_id == "candidate_llm_valid"


def test_pipeline_rejects_missing_evidence_id():
    payload = _payload()
    payload["achievement_events"][0]["evidence_id"] = "missing_evidence"
    result = ExtractionPipeline().validate_payload(payload)
    assert result.passed is False
    assert any("证据引用校验失败" in error for error in result.errors)


def test_pipeline_rejects_masked_for_scoring_false():
    payload = _payload()
    payload["sensitive_information"]["masked_for_scoring"] = False
    result = ExtractionPipeline().validate_payload(payload)
    assert result.passed is False
    assert any("Schema" in error or "Pydantic" in error for error in result.errors)


def test_pipeline_rejects_sensitive_quote_leak():
    payload = _payload()
    payload["evidence_items"][0]["quote"] = "电话：13812345678，完成招聘配置。"
    result = ExtractionPipeline().validate_payload(payload)
    assert result.passed is False
    assert result.rejected_due_to_sensitive_content is True


def test_failed_pipeline_does_not_save(tmp_path):
    payload = _payload()
    payload["evidence_items"] = []
    path = tmp_path / "bad.json"
    result = ExtractionPipeline().validate_payload(payload, save_path=path)
    assert result.passed is False
    assert not path.exists()
