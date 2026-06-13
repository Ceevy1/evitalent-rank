def test_report_service_generates_safe_html(tmp_path):
    from evitalent.extraction.mock_extractor import MockExtractor
    from evitalent.scoring.ranker import rank_candidates
    from evitalent.services.report_service import ReportService

    candidates = [c for c in MockExtractor().load_all() if any(item.domain == "hr" for item in c.candidate_profile.target_domain_candidates)]
    result = rank_candidates(candidates, "hr", ranking_id="test_report")
    path = ReportService().generate_ranking_report(result, tmp_path / "report.html")
    html = path.read_text(encoding="utf-8")
    assert "RankScore" in html
    assert "demo_hr_001" in html
    assert "13900001234" not in html
    assert "28K" not in html
    assert "陆晨" not in html
