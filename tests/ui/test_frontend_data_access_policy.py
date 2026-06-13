from __future__ import annotations

from pathlib import Path


def test_frontend_safe_view_models_do_not_read_private_manifest():
    source = Path("app/safe_view_models.py").read_text(encoding="utf-8")
    assert "raw_manifest_private" not in source
    assert "extraction_results_private" not in source


def test_technical_acceptance_expander_default_collapsed():
    source = Path("app/components/technical_acceptance_expander.py").read_text(encoding="utf-8")
    assert "expanded=False" in source
    assert "Prompt" not in source
    assert "API key" not in source
