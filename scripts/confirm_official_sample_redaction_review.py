from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.redaction_review_gate import confirm_redaction_review
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Confirm manual review of all pilot redacted texts.")
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("This command requires --confirm after manual review of all pilot redacted texts.")
    settings = load_official_sample_settings()
    payload = confirm_redaction_review(settings)
    print(f"review_confirmed={payload['review_confirmed']}")
    print(f"gate={settings.review_gate_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
