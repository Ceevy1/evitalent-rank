from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.audit.timeline_audit import run_timeline_audit
from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.models.extraction import CandidateExtraction


def _domain_candidates(domain: str):
    return [c for c in MockExtractor().load_all() if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]


def main() -> None:
    candidates = _domain_candidates("hr") + _domain_candidates("production")
    normal = run_timeline_audit(candidates)
    broken_payload = candidates[0].model_dump(mode="json")
    broken_payload["career_records"][1]["start_date"] = broken_payload["career_records"][0]["start_date"]
    broken = CandidateExtraction.model_validate(broken_payload)
    conflict = run_timeline_audit(broken)
    print(f"normal_issue_count={normal['issue_count']}")
    print(f"conflict_issue_count={conflict['issue_count']}")
    print(f"conflict_critical_count={conflict['critical_issue_count']}")
    print(f"penalty_recommendation={conflict['penalty_recommendation']}")


if __name__ == "__main__":
    main()
