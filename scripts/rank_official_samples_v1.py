from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.official_samples.domain_ranking_runner import DomainRankingRunner
from evitalent.official_samples.settings import load_official_sample_settings


def main() -> int:
    settings = load_official_sample_settings()
    result = DomainRankingRunner(settings).run(include_partial=True)
    for domain, payload in result["domains"].items():
        print(f"{domain} | ranked={payload['candidate_count']} | excluded={payload['excluded_counts']}")
    print(f"safe_summary={settings.rankings_dir / 'all_domains_safe_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
