from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = [
    "domain_weights",
    "extraction_comparison",
    "fictional_docx_e2e_results",
    "official_sample_processing_stats",
    "ablation_experiments",
    "privacy_safety_checks",
    "assistant_qa_examples",
]

FORBIDDEN_TERMS = [
    "姓名",
    "电话",
    "邮箱",
    "婚姻",
    "薪资",
    "原始文件名",
    "phone",
    "email",
    "marital",
    "salary",
    "original_filename",
    "private_relative_path",
    "data/raw",
    "data/redacted",
]


def test_export_report_materials_generates_safe_csv_and_markdown(tmp_path):
    output_dir = tmp_path / "report_materials"

    result = subprocess.run(
        [sys.executable, "scripts/export_report_materials.py", "--output-dir", str(output_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "generated_files=" in result.stdout
    for table in EXPECTED_TABLES:
        assert (output_dir / f"{table}.csv").exists()
        assert (output_dir / f"{table}.md").exists()
    assert "```mermaid" in (output_dir / "model_algorithm_flow.md").read_text(encoding="utf-8")
    assert (output_dir / "innovation_summary.md").exists()
    assert (output_dir / "report_ready_summary.md").exists()

    combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in output_dir.glob("*.*"))
    for term in FORBIDDEN_TERMS:
        assert term not in combined
