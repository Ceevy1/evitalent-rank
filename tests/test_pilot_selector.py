from __future__ import annotations

from evitalent.official_samples.inventory_service import OfficialInventoryService
from evitalent.official_samples.pilot_selector import select_redaction_pilot_documents
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import DOMAINS, make_private_tree, write_docx


def test_pilot_selector_one_per_domain_and_deterministic(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    write_docx(input_root / "hr" / "aaa_extra.docx", ["候选人编号：Y", "招聘完成率提升至91%。"])
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    manifest = OfficialInventoryService(settings).scan()

    first = select_redaction_pilot_documents(manifest, settings.domains)
    second = select_redaction_pilot_documents(manifest, settings.domains)
    assert [item.document_id for item in first] == [item.document_id for item in second]
    assert {item.folder_domain for item in first} == set(DOMAINS)
    assert len(first) == 6
