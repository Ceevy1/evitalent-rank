from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.safe_summary_builder import build_safe_html_report
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    settings = load_official_sample_settings()
    path = build_safe_html_report(settings)
    print(f"safe_report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
