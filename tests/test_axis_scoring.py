import pytest

from evitalent.extraction.mock_extractor import MockExtractor
from evitalent.scoring.axis_scorer import AXES, load_domain_weight_config, score_candidate_axes


def test_axis_scores_in_range_and_weights_load():
    candidate = MockExtractor().extract("demo_hr_001")
    result = score_candidate_axes(candidate, "hr")
    assert set(result.axis_scores) == set(AXES)
    assert all(0 <= score <= 100 for score in result.axis_scores.values())
    cfg = load_domain_weight_config()
    assert "hr" in cfg["domains"]


def test_bad_weight_sum_raises(tmp_path):
    path = tmp_path / "bad_weights.yaml"
    weights = {axis: 0.1 for axis in AXES}
    weights["education"] = 0.2
    lines = ["version: 'x'", "domains:", "  hr:", "    label: 'HR'", "    weights:"]
    lines.extend([f"      {axis}: {value}" for axis, value in weights.items()])
    lines.extend(["ranking:", "  evidence_floor: 0.85", "  evidence_adjustment_weight: 0.15", "  max_penalty: 8.0", "  missing_axis_neutral_score: 50.0"])
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError):
        load_domain_weight_config(path)
