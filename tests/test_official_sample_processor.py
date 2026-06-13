from __future__ import annotations

import pytest

from evitalent.official_samples.inventory_service import OfficialInventoryService
from evitalent.official_samples.official_sample_processor import OfficialSampleProcessor
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import make_private_tree


def test_official_processor_requires_private_input_and_blocks_unsafe_text(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    record = OfficialInventoryService(settings).scan().documents[0]
    processor = OfficialSampleProcessor(settings)

    assert processor.private_path(record).is_relative_to(input_root)
    with pytest.raises(ValueError):
        processor.run_local_ollama_extraction("doc", "hr", "手机号：13900001111")


def test_official_processor_separates_folder_and_detected_domains_without_rewrite(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    processor = OfficialSampleProcessor(settings)

    class FakeClient:
        provider = "local_ollama"
        request_count = 0
        def generate_json(self, system_prompt, user_prompt):
            self.request_count += 1
            return {"target_domains": ["hr"], "highest_role_level": "manager"}

    result = processor.run_local_ollama_extraction("doc", "production", "完成招聘18人", client=FakeClient())  # type: ignore[arg-type]
    assert result["folder_domain"] == "production"
    assert result["detected_domains"] == ["hr"]
    assert result["domain_match_status"] == "mismatch_needs_review"

    settings_dict = settings.__dict__.copy()
    assert settings_dict["allow_mock_fallback"] is False
