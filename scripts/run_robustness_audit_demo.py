from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.audit.robustness_audit import run_robustness_audit
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.settings import PROJECT_ROOT


def main() -> None:
    candidates = [c for c in MockExtractor().load_all() if any(item.domain == "hr" for item in c.candidate_profile.target_domain_candidates)]
    audit = run_robustness_audit(candidates, candidates, candidates, "hr", top_k=3)
    output_dir = PROJECT_ROOT / "data" / "outputs" / "audit_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "robustness_demo_hr.json"
    path.write_text(__import__("json").dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"robustness_status={audit['robustness_audit_status']}")
    print(f"top3_consistency={audit['comparisons']['fact_only_text']['top_k_consistency']}")
    print(f"mean_rank_shift={audit['comparisons']['fact_only_text']['mean_rank_shift']}")
    print(f"max_rank_shift={audit['comparisons']['fact_only_text']['max_rank_shift']}")
    print(f"saved={path}")


if __name__ == "__main__":
    main()
