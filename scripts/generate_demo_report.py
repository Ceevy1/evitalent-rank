from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.reporting.html_report import generate_html_report
from evitalent.scoring.ranker import rank_candidates


def main() -> None:
    candidates = MockExtractor().load_all()
    result = rank_candidates(candidates, "hr", ranking_id="demo_hr_report")
    path = generate_html_report(result)
    print(path)


if __name__ == "__main__":
    main()
