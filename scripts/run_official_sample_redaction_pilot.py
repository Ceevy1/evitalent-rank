from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.official_sample_processor import OfficialSampleProcessor, save_redaction_pilot_outputs
from evitalent.official_samples.pilot_selector import select_redaction_pilot_documents
from evitalent.official_samples.private_manifest import load_private_manifest
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    settings = load_official_sample_settings()
    if not settings.raw_manifest_path.exists():
        raise SystemExit("Missing raw manifest. Run scripts/audit_official_sample_inventory.py first.")
    manifest = load_private_manifest(settings.raw_manifest_path)
    selected = select_redaction_pilot_documents(manifest, settings.domains)
    if len(selected) != len(settings.domains):
        missing = sorted(set(settings.domains) - {item.folder_domain for item in selected})
        raise SystemExit(f"Could not select one readable non-duplicate DOCX for every domain: {', '.join(missing)}")
    processor = OfficialSampleProcessor(settings)
    rows = [processor.parse_and_redact(record) for record in selected]
    save_redaction_pilot_outputs(settings, rows)
    print("domain | document_id | parse_status | redaction_status | safety_passed | warning_count | redacted_output_path")
    for row in rows:
        print(
            f"{row.domain} | {row.document_id} | {row.parse_status} | {row.redaction_status} | "
            f"{row.safety_passed} | {row.warning_count} | {row.redacted_output_path}"
        )
    print(f"private_result={settings.redaction_pilot_private_path}")
    print(f"safe_summary={settings.redaction_pilot_safe_summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
