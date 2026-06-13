from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.batch_extraction_runner import OfficialBatchExtractionRunner
from evitalent.official_samples.private_manifest import load_private_manifest
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    settings = load_official_sample_settings()
    manifest = load_private_manifest(settings.raw_manifest_path)
    summary = OfficialBatchExtractionRunner(settings).run(manifest, resume=args.resume)
    for row in summary:
        print(
            f"{row['domain']} | processed={row['processed_documents']} | "
            f"eligible={row['eligible_documents']} | failed={row['failed_documents']}"
        )
    print(f"batch_state={settings.batch_state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
