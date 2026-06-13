import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_REAL_OLLAMA_TESTS") != "true", reason="RUN_REAL_OLLAMA_TESTS=true is required")
def test_real_ollama_docx_e2e():
    completed = subprocess.run(
        [sys.executable, "scripts/run_real_ollama_docx_e2e_demo.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=True,
    )
    assert "used_mock_response" in completed.stdout
    summary_path = ROOT / "data" / "outputs" / "audit_reports" / "real_ollama_docx_e2e_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["actual_llm_request_count"] >= 15
    assert summary["used_mock_response"] is False
    assert summary["used_cached_response"] is False
    assert summary["sensitive_leakage_count"] == 0
    assert summary["event_recall"] == 1.0
    assert summary["numeric_exact_match"] == 1.0
    assert summary["normalization_accuracy"] == 1.0
    assert summary["grounding_pass_rate"] == 1.0
    assert all(doc["eligible_for_scoring"] for doc in summary["documents"])
