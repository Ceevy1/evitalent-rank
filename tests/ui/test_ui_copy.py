from __future__ import annotations

from app.ui_copy import FIELD_LABELS, STATUS_LABELS, label_for_domain, label_for_status


def test_internal_status_and_fields_have_business_labels():
    assert FIELD_LABELS["RankScore"] == "综合竞争力指数"
    assert FIELD_LABELS["BCS"] == "能力表现分"
    assert FIELD_LABELS["ECI"] == "材料可信度"
    assert FIELD_LABELS["Penalty"] == "风险扣减"
    assert STATUS_LABELS["failed_grounding"] == "成果依据无法核验"
    assert STATUS_LABELS["local_ollama"] == "本地智能分析服务"
    assert label_for_status("completed_eligible") == "可纳入比较"
    assert label_for_domain("hr") == "人力资源"
