from __future__ import annotations

from evitalent.official_samples.inventory_service import OfficialInventoryService, build_inventory_safe_summary
from evitalent.official_samples.private_manifest import load_private_manifest, save_private_manifest
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import make_private_tree, write_docx


def test_private_manifest_saves_private_fields_and_safe_summary_removes_paths(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    write_docx(input_root / "hr" / "duplicate.docx", ["候选人编号：X", "领域：hr", "工作经历：负责流程优化，完成招聘18人。"])
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    manifest = OfficialInventoryService(settings).scan()

    save_private_manifest(manifest, settings.raw_manifest_path)
    loaded = load_private_manifest(settings.raw_manifest_path)
    assert loaded.documents[0].original_filename
    assert any(item.duplicate_within_domain for item in loaded.documents if item.folder_domain == "hr")

    safe = build_inventory_safe_summary(loaded, settings.domains)
    safe_text = str(safe)
    assert "original_filename" not in safe_text
    assert "private_relative_path" not in safe_text
