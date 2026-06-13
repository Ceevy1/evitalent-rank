from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evitalent.official_samples.private_manifest import read_json, write_json


ISSUE_CONFIRMED_RESOLVED = "issue_confirmed_resolved"
ISSUE_RISK_RETAINED = "issue_risk_retained"
ISSUE_NEEDS_MATERIAL = "issue_needs_material"

VALID_ISSUE_DECISIONS = {ISSUE_CONFIRMED_RESOLVED, ISSUE_RISK_RETAINED, ISSUE_NEEDS_MATERIAL}


def review_key(document_id: str, issue: str) -> str:
    return f"{document_id}::{issue}"


@dataclass
class RiskIssueReviewStore:
    path: Path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"issue_reviews": {}}
        payload = read_json(self.path)
        payload.setdefault("issue_reviews", {})
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        write_json(self.path, payload)

    def record(
        self,
        document_id: str,
        *,
        domain: str,
        issue: str,
        decision: str,
        reviewer: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        if decision not in VALID_ISSUE_DECISIONS:
            raise ValueError(f"Unsupported risk issue review decision: {decision}")
        clean_issue = issue.strip()
        if not clean_issue:
            raise ValueError("Risk issue must not be empty.")
        payload = self.load()
        review = {
            "document_id": document_id,
            "domain": domain,
            "issue": clean_issue,
            "review_status": decision,
            "reviewer": reviewer.strip() or "人工审核员",
            "note": note.strip(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        payload["issue_reviews"][review_key(document_id, clean_issue)] = review
        self.save(payload)
        return review

    def summary(self) -> dict[str, int]:
        reviews = self.load().get("issue_reviews", {})
        return {
            "reviewed_issues": len(reviews),
            "resolved_issues": sum(1 for item in reviews.values() if item.get("review_status") == ISSUE_CONFIRMED_RESOLVED),
            "retained_issues": sum(1 for item in reviews.values() if item.get("review_status") == ISSUE_RISK_RETAINED),
            "needs_material_issues": sum(1 for item in reviews.values() if item.get("review_status") == ISSUE_NEEDS_MATERIAL),
        }
