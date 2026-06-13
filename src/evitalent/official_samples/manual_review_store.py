from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evitalent.official_samples.batch_state_store import (
    COMPLETED_NEEDS_REVIEW,
    FAILED_GROUNDING,
    FAILED_MODEL_REQUEST,
    FAILED_SCHEMA,
    FAILED_UNKNOWN,
)
from evitalent.official_samples.private_manifest import read_json, write_json


MANUAL_APPROVED = "manual_approved"
MANUAL_REJECTED = "manual_rejected"
MANUAL_NEEDS_FOLLOW_UP = "manual_needs_follow_up"

REVIEWABLE_SOURCE_STATUSES = {
    COMPLETED_NEEDS_REVIEW,
    FAILED_SCHEMA,
    FAILED_GROUNDING,
    FAILED_MODEL_REQUEST,
    FAILED_UNKNOWN,
}

VALID_DECISIONS = {MANUAL_APPROVED, MANUAL_REJECTED, MANUAL_NEEDS_FOLLOW_UP}


@dataclass
class ManualReviewStore:
    path: Path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"reviews": {}}
        payload = read_json(self.path)
        payload.setdefault("reviews", {})
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        write_json(self.path, payload)

    def record(
        self,
        document_id: str,
        *,
        domain: str,
        source_status: str,
        decision: str,
        reviewer: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        if source_status not in REVIEWABLE_SOURCE_STATUSES:
            raise ValueError(f"Status is not eligible for manual review: {source_status}")
        if decision not in VALID_DECISIONS:
            raise ValueError(f"Unsupported manual review decision: {decision}")
        payload = self.load()
        review = {
            "document_id": document_id,
            "domain": domain,
            "source_status": source_status,
            "manual_status": decision,
            "reviewer": reviewer.strip() or "人工审核员",
            "note": note.strip(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        payload["reviews"][document_id] = review
        self.save(payload)
        return review

    def summary(self) -> dict[str, int]:
        reviews = self.load().get("reviews", {})
        return {
            "reviewed_documents": len(reviews),
            "approved_documents": sum(1 for item in reviews.values() if item.get("manual_status") == MANUAL_APPROVED),
            "rejected_documents": sum(1 for item in reviews.values() if item.get("manual_status") == MANUAL_REJECTED),
            "follow_up_documents": sum(1 for item in reviews.values() if item.get("manual_status") == MANUAL_NEEDS_FOLLOW_UP),
        }
