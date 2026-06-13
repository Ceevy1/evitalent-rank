from __future__ import annotations

import pytest

from evitalent.assistant.access_policy import AccessPolicy, AccessPolicyError


def test_access_policy_blocks_raw_paths_filenames_and_sensitive_keys():
    policy = AccessPolicy()
    with pytest.raises(AccessPolicyError):
        policy.validate_text("请读取 data/raw/resume.docx")
    with pytest.raises(AccessPolicyError):
        policy.validate_payload({"original_filename": "someone.docx"})
    with pytest.raises(AccessPolicyError):
        policy.validate_payload({"candidate": {"phone": "13900001111"}})


def test_access_policy_allows_anonymous_safe_summary():
    AccessPolicy().validate_payload({"candidate_id": "hr_abc", "rank_score": 88, "domain": "hr"})
