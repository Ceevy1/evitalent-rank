from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.batch_extraction_runner import OfficialBatchExtractionRunner
from evitalent.official_samples.domain_ranking_runner import DomainRankingRunner
from evitalent.official_samples.inventory_service import OfficialInventoryService, build_inventory_safe_summary
from evitalent.official_samples.official_sample_processor import OfficialSampleProcessor, save_redaction_pilot_outputs
from evitalent.official_samples.pilot_selector import select_redaction_pilot_documents
from evitalent.official_samples.private_manifest import load_private_manifest, write_json
from evitalent.official_samples.redaction_review_gate import confirm_redaction_review
from evitalent.official_samples.safe_summary_builder import build_safe_html_report
from evitalent.official_samples.settings import load_official_sample_settings


def _set_project_dataset_defaults() -> None:
    os.environ.setdefault("EVITALENT_PRIVATE_DATA_ROOT", str(ROOT / "data"))
    os.environ.setdefault("RESUME_INPUT_ROOT", str(ROOT / "data" / "raw" / "resumes"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the official resume dataset through redaction, Ollama extraction, ranking, and safe report export.")
    parser.add_argument("--resume", action="store_true", help="Resume batch extraction from the existing checkpoint.")
    parser.add_argument("--skip-pilot-llm", action="store_true", help="Skip pilot LLM if a safe pilot summary already exists.")
    args = parser.parse_args()

    _set_project_dataset_defaults()
    settings = load_official_sample_settings(create_dirs=True)

    inventory = OfficialInventoryService(settings)
    manifest = inventory.scan()
    inventory.save_outputs(manifest)
    inventory_rows = build_inventory_safe_summary(manifest, settings.domains)
    print("inventory")
    for row in inventory_rows:
        print(f"{row['domain']} | documents={row['document_count']} | readable={row['readable_count']} | unreadable={row['unreadable_count']} | duplicates={row['duplicate_count']}")

    selected = select_redaction_pilot_documents(manifest, settings.domains)
    processor = OfficialSampleProcessor(settings)
    pilot_rows = [processor.parse_and_redact(record) for record in selected]
    save_redaction_pilot_outputs(settings, pilot_rows)
    confirm_redaction_review(settings)
    print(f"redaction_pilot={settings.redaction_pilot_safe_summary_path}")

    if args.skip_pilot_llm and settings.llm_pilot_safe_summary_path.exists():
        print(f"llm_pilot=existing:{settings.llm_pilot_safe_summary_path}")
    else:
        pilot_results = []
        for domain in settings.domains:
            redacted_files = sorted((settings.redacted_pilot_dir / domain).glob("*.txt"))
            if not redacted_files:
                raise RuntimeError(f"Missing pilot redacted text for {domain}")
            path = redacted_files[0]
            print(f"pilot_llm | {domain} | {path.stem} | started", flush=True)
            result = processor.run_local_ollama_extraction(path.stem, domain, path.read_text(encoding="utf-8"))
            pilot_results.append(result)
            print(f"pilot_llm | {domain} | eligible={result['eligible_for_scoring']} | grounded={result['grounded_event_count']} | requests={result['actual_llm_request_count']}", flush=True)
        safe_pilot_results = [{key: value for key, value in row.items() if key != "candidate_extraction"} for row in pilot_results]
        write_json(settings.llm_pilot_private_path, {"documents": pilot_results})
        write_json(settings.llm_pilot_safe_summary_path, {"documents": safe_pilot_results})
        print(f"llm_pilot={settings.llm_pilot_safe_summary_path}")

    manifest = load_private_manifest(settings.raw_manifest_path)
    batch_summary = OfficialBatchExtractionRunner(settings).run(manifest, resume=args.resume)
    print("batch")
    for row in batch_summary:
        print(f"{row['domain']} | processed={row['processed_documents']} | eligible={row['eligible_documents']} | needs_review={row['needs_review_documents']} | failed={row['failed_documents']}")

    ranking = DomainRankingRunner(settings).run(include_partial=True)
    print("ranking")
    for domain, payload in ranking["domains"].items():
        print(f"{domain} | ranked={payload['candidate_count']} | excluded={payload['excluded_counts']}")

    report_path = build_safe_html_report(settings)
    print(f"safe_inventory={settings.inventory_safe_summary_path}")
    print(f"safe_processing={settings.batch_output_dir / 'safe_processing_summary.json'}")
    print(f"safe_ranking={settings.rankings_dir / 'all_domains_safe_summary.json'}")
    print(f"safe_report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
