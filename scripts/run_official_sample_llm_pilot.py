from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.official_sample_processor import OfficialSampleProcessor
from evitalent.official_samples.private_manifest import load_private_manifest, write_json
from evitalent.official_samples.redaction_review_gate import assert_llm_pilot_allowed
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    settings = load_official_sample_settings()
    assert_llm_pilot_allowed(settings)
    manifest = load_private_manifest(settings.raw_manifest_path)
    processor = OfficialSampleProcessor(settings)
    rows = []
    for domain in settings.domains:
        redacted_files = sorted((settings.redacted_pilot_dir / domain).glob("*.txt"))
        if not redacted_files:
            raise SystemExit(f"Missing pilot redacted text for {domain}")
        path = redacted_files[0]
        document_id = path.stem
        print(f"{domain} | {document_id} | status=started", flush=True)
        result = processor.run_local_ollama_extraction(document_id, domain, path.read_text(encoding="utf-8"))
        rows.append(result)
        print(
            f"{domain} | {document_id} | eligible={result['eligible_for_scoring']} | "
            f"grounded={result['grounded_event_count']} | llm_requests={result['actual_llm_request_count']}",
            flush=True,
        )
    safe_rows = [{key: value for key, value in row.items() if key != "candidate_extraction"} for row in rows]
    write_json(settings.llm_pilot_private_path, {"documents": rows})
    write_json(settings.llm_pilot_safe_summary_path, {"documents": safe_rows})
    print(f"private_result={settings.llm_pilot_private_path}")
    print(f"safe_summary={settings.llm_pilot_safe_summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
