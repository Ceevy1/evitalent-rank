from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.ranker import rank_candidates


def _domain_candidates(domain: str):
    candidates = MockExtractor().load_all()
    return [c for c in candidates if any(item.domain == domain for item in c.candidate_profile.target_domain_candidates)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="hr", choices=["ecommerce", "brand", "hr", "production", "sales", "rd"])
    args = parser.parse_args()

    candidates = _domain_candidates(args.domain)
    result = rank_candidates(candidates, args.domain, ranking_id=f"demo_{args.domain}_stage4")
    output_dir = ROOT / "data" / "outputs" / "rankings"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{result.ranking_id}.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    print(f"domain={result.domain} label={result.domain_label} candidates={len(result.candidates)}")
    print("rank | candidate_id | BCS | ECI | Penalty | RankScore | top_strengths | risk_flags")
    for item in result.candidates:
        strengths = ",".join(strength.label for strength in item.top_strengths)
        risks = ",".join(item.risk_flags[:3])
        print(f"{item.rank} | {item.candidate_id} | {item.bcs:.2f} | {item.eci:.2f} | {item.penalty:.2f} | {item.rank_score:.2f} | {strengths} | {risks}")
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
