from __future__ import annotations

import json
from pathlib import Path

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.reporting.html_report import generate_html_report
from evitalent.scoring.ranker import rank_candidates
from evitalent.settings import PROJECT_ROOT


def main() -> None:
    candidates = MockExtractor().load_all()
    output_dir = PROJECT_ROOT / "data" / "outputs" / "rankings"
    output_dir.mkdir(parents=True, exist_ok=True)
    for domain in ["ecommerce", "brand", "hr", "production", "sales", "rd"]:
        result = rank_candidates(candidates, domain, ranking_id=f"demo_{domain}")
        out_path = output_dir / f"{result.ranking_id}.json"
        out_path.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        report_path = generate_html_report(result)
        print(f"{domain}: top={result.results[0].display_id}, report={report_path}")


if __name__ == "__main__":
    main()

