from evitalent.audit.audit_report_builder import build_audit_result


def test_audit_report_contains_limitations():
    audit = build_audit_result("ranking_x", "hr", fairness_audit={"max_rank_shift": 0, "max_score_shift": 0, "detected_issues": []})
    assert audit.limitations
    assert audit.overall_conclusion.overall_audit_status == "passed"


def test_failed_audit_not_marked_passed():
    fairness = {
        "max_rank_shift": 1,
        "max_score_shift": 1,
        "detected_issues": [{"severity": "critical", "description": "leak"}],
    }
    audit = build_audit_result("ranking_x", "hr", fairness_audit=fairness)
    assert audit.overall_conclusion.overall_audit_status == "failed"
