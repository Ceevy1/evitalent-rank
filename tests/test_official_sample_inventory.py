from __future__ import annotations

from evitalent.official_samples.inventory_service import OfficialInventoryService, build_inventory_safe_summary
from evitalent.official_samples.private_manifest import anonymous_document_id, sha256_file
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import DOMAINS, make_private_tree


def test_inventory_reads_six_domains_docx_only_and_safe_summary_hides_filenames(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)

    manifest = OfficialInventoryService(settings).scan()
    assert {item.folder_domain for item in manifest.documents} == set(DOMAINS)
    assert len(manifest.documents) == 6
    assert all(item.original_filename.endswith(".docx") for item in manifest.documents)

    first = manifest.documents[0]
    assert first.document_id == anonymous_document_id(first.folder_domain, sha256_file(input_root / first.private_relative_path))
    summary = build_inventory_safe_summary(manifest, settings.domains)
    assert len(summary) == 6
    assert "original_filename" not in str(summary)
    assert "sample.docx" not in str(summary)
