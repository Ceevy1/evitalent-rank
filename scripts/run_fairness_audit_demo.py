from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.audit.fairness_audit import run_fairness_audit
from evitalent.extraction.mock_extractor import MockExtractor


def main() -> None:
    candidates = [c for c in MockExtractor().load_all() if any(item.domain == "hr" for item in c.candidate_profile.target_domain_candidates)]
    audit = run_fairness_audit(candidates, "hr")
    print(f"fairness_status={audit['fairness_audit_status']}")
    print(f"max_score_shift={audit['max_score_shift']}")
    print(f"max_rank_shift={audit['max_rank_shift']}")
    print(f"mean_rank_shift={audit['mean_rank_shift']}")


if __name__ == "__main__":
    main()
