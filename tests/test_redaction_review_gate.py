from __future__ import annotations

import pytest

from evitalent.official_samples.official_sample_processor import RedactionPilotResult, save_redaction_pilot_outputs
from evitalent.official_samples.redaction_review_gate import RedactionReviewGateError, assert_llm_pilot_allowed, confirm_redaction_review
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import DOMAINS, make_private_tree


def _row(domain: str, safe: bool = True) -> RedactionPilotResult:
    return RedactionPilotResult(
        document_id=f"{domain}_abc",
        domain=domain,
        parse_status="success",
        redaction_status="passed" if safe else "failed_safety",
        detected_pii_type_counts={},
        safety_passed=safe,
        warning_count=0,
        redacted_output_path=f"redacted/resumes/pilot/{domain}/{domain}_abc.txt",
    )


def test_review_gate_blocks_before_confirm_and_allows_after(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    rows = [_row(domain) for domain in DOMAINS]
    save_redaction_pilot_outputs(settings, rows)
    for row in rows:
        (settings.private_data_root / row.redacted_output_path).parent.mkdir(parents=True, exist_ok=True)
        (settings.private_data_root / row.redacted_output_path).write_text("已脱敏文本", encoding="utf-8")

    with pytest.raises(RedactionReviewGateError):
        assert_llm_pilot_allowed(settings)
    confirm_redaction_review(settings)
    assert_llm_pilot_allowed(settings)


def test_review_gate_rejects_any_safety_failed(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    rows = [_row(domain, safe=(domain != "hr")) for domain in DOMAINS]
    save_redaction_pilot_outputs(settings, rows)
    with pytest.raises(RedactionReviewGateError):
        confirm_redaction_review(settings)
