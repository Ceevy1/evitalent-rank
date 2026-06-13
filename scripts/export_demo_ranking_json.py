from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates


DOMAINS = ["ecommerce", "brand", "hr", "production", "sales", "rd"]


def main() -> None:
    all_candidates = MockExtractor().load_all()
    output_dir = ROOT / "data" / "outputs" / "rankings"
    output_dir.mkdir(parents=True, exist_ok=True)
    for domain in DOMAINS:
        candidates = [c for c in all_candidates if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]
        result = rank_candidates(candidates, domain, ranking_id=f"demo_{domain}_stage4")
        path = output_dir / f"{result.ranking_id}.json"
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print({"domain": domain, "candidate_count": len(candidates), "insufficient_candidates_for_ranking": result.insufficient_candidates_for_ranking, "saved": str(path)})


if __name__ == "__main__":
    main()
