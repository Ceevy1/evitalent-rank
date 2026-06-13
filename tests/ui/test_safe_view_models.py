from __future__ import annotations

from app.safe_view_models import (
    attach_risk_issue_review_status,
    filter_formal_ranking,
    has_forbidden_view_keys,
    manual_review_rows,
    official_ranking_rows,
    overview_metrics,
    risk_issue_review_rows,
    split_risk_issues,
)


def test_safe_view_model_excludes_forbidden_keys_and_filters_formal_ranking():
    assert has_forbidden_view_keys({"candidate_id": "hr_001", "rank_score": 90}) is False
    assert has_forbidden_view_keys({"phone": "13900001111"}) is True
    assert has_forbidden_view_keys({"profile": {"salary_current": "30k"}}) is True

    rows = [
        {"status": "completed_eligible", "candidate_id": "a"},
        {"status": "completed_needs_review", "candidate_id": "b"},
        {"status": "failed_safety", "candidate_id": "c"},
        {"status": "manual_approved", "candidate_id": "d"},
    ]
    assert [row["candidate_id"] for row in filter_formal_ranking(rows)] == ["a", "d"]


def test_official_ranking_rows_are_business_named():
    workspace = {
        "rankings": {
            "domains": {
                "hr": {
                    "ranking": [
                        {
                            "rank": 1,
                            "document_id": "hr_abc",
                            "rank_score": 88,
                            "bcs": 82,
                            "eci": 95,
                            "penalty": 0,
                            "top_strength_labels": ["招聘交付"],
                            "risk_flag_types": [],
                            "grounded_achievement_count": 3,
                        }
                    ]
                }
            }
        }
    }
    rows = official_ranking_rows(workspace, "hr")
    assert rows[0]["候选人编号"] == "hr_abc"
    assert rows[0]["综合竞争力指数"] == 88
    assert "rank_score" not in rows[0]


def test_overview_metrics_handles_empty_data():
    metrics = overview_metrics({"rankings": {"domains": {}}, "batch": []})
    assert metrics["已分析简历数"] == 0
    assert metrics["可纳入比较人数"] == 0


def test_manual_review_rows_include_reviewable_batch_state_only():
    workspace = {
        "batch_state": {
            "documents": {
                "hr_a": {"document_id": "hr_a", "domain": "hr", "status": "completed_needs_review"},
                "hr_b": {"document_id": "hr_b", "domain": "hr", "status": "completed_eligible"},
            }
        },
        "manual_review": {"reviews": {"hr_a": {"manual_status": "manual_approved", "note": "已确认"}}},
    }

    rows = manual_review_rows(workspace)

    assert len(rows) == 1
    assert rows[0]["候选人编号"] == "hr_a"
    assert rows[0]["人工核验状态"] == "人工核验通过"


def test_risk_issue_review_rows_and_status_are_anonymous():
    rows = [{"候选人编号": "brand_a", "待核验事项": "achievement 证据不足、match 证据不足"}]
    workspace = {
        "risk_issue_review": {
            "issue_reviews": {
                "brand_a::achievement 证据不足": {
                    "review_status": "issue_confirmed_resolved",
                    "note": "已确认",
                }
            }
        }
    }

    assert split_risk_issues(rows[0]["待核验事项"]) == ["achievement 证据不足", "match 证据不足"]
    reviewed_rows = risk_issue_review_rows(rows, workspace, "brand")
    status_rows = attach_risk_issue_review_status(rows, workspace)

    assert len(reviewed_rows) == 2
    assert reviewed_rows[0]["处理状态"] == "已核验通过"
    assert status_rows[0]["待核验处理状态"] == "已处理 1/2"
    assert status_rows[0]["待处理事项数"] == 1
