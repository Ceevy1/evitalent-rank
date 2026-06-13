from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.evidence_linker import check_evidence_links
from evitalent.extraction.mock_extractor import MockExtractor


def main() -> None:
    extractor = MockExtractor()
    files = sorted(extractor.fixture_dir.glob("*.json"))
    passed = 0
    failed = 0

    for path in files:
        try:
            candidate = extractor.extract(path.stem)
            link_result = check_evidence_links(candidate)
            ok = link_result["passed"]
            passed += int(ok)
            failed += int(not ok)
            domains = [item.domain for item in candidate.candidate_profile.target_domain_candidates]
            print(
                {
                    "candidate_id": candidate.candidate_id,
                    "recommended_domains": domains,
                    "career_records": len(candidate.career_records),
                    "achievement_events": len(candidate.achievement_events),
                    "evidence_items": len(candidate.evidence_items),
                    "validation_passed": ok,
                }
            )
        except Exception as exc:
            failed += 1
            print({"fixture": path.name, "validation_passed": False, "error": str(exc)})

    ready = failed == 0 and passed >= 8
    print({"passed_count": passed, "failed_count": failed, "ready_for_scoring_stage": ready})


if __name__ == "__main__":
    main()
