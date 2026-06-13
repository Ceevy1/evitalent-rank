from __future__ import annotations

from evitalent.official_samples.private_manifest import write_json
from evitalent.official_samples.safe_summary_builder import build_safe_html_report
from evitalent.official_samples.settings import load_official_sample_settings
from official_samples_test_utils import make_private_tree


def test_safe_summary_html_excludes_sensitive_fields_and_contains_boundaries(tmp_path, monkeypatch):
    input_root = make_private_tree(tmp_path)
    monkeypatch.setenv("EVITALENT_PRIVATE_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("RESUME_INPUT_ROOT", str(input_root))
    settings = load_official_sample_settings(create_dirs=True)
    write_json(settings.inventory_safe_summary_path, [{"domain": "hr", "document_count": 2, "readable_count": 2, "unreadable_count": 0}])
    write_json(
        settings.rankings_dir / "all_domains_safe_summary.json",
        {
            "domains": {
                "hr": {
                    "candidate_count": 1,
                    "excluded_counts": {"failed_safety": 1},
                    "ranking": [
                        {
                            "rank": 1,
                            "document_id": "hr_abc",
                            "bcs": 70,
                            "eci": 90,
                            "penalty": 0,
                            "rank_score": 68,
                            "top_strength_labels": ["achievement"],
                            "risk_flag_types": ["evidence"],
                        }
                    ],
                }
            }
        },
    )
    path = build_safe_html_report(settings)
    html = path.read_text(encoding="utf-8")
    assert "结果为辅助评价，不是录用决定" in html
    assert "failed_safety" not in html  # exclusion details stay in JSON summary, not report table
    assert "13900001111" not in html
    assert "sample.docx" not in html
