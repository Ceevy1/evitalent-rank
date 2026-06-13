from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.inventory_service import OfficialInventoryService, build_inventory_safe_summary
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    settings = load_official_sample_settings()
    service = OfficialInventoryService(settings)
    manifest = service.scan()
    service.save_outputs(manifest)
    rows = build_inventory_safe_summary(manifest, settings.domains)
    print("domain | document_count | readable_count | unreadable_count | duplicate_count")
    for row in rows:
        print(
            f"{row['domain']} | {row['document_count']} | {row['readable_count']} | "
            f"{row['unreadable_count']} | {row['duplicate_count']}"
        )
    print(f"private_manifest={settings.raw_manifest_path}")
    print(f"safe_summary={settings.inventory_safe_summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
