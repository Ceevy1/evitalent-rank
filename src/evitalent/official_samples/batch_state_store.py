from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evitalent.official_samples.private_manifest import read_json, write_json


PENDING = "pending"
PROCESSING = "processing"
COMPLETED_ELIGIBLE = "completed_eligible"
COMPLETED_NEEDS_REVIEW = "completed_needs_review"
FAILED_REDACTION = "failed_redaction"
FAILED_SCHEMA = "failed_schema"
FAILED_GROUNDING = "failed_grounding"
FAILED_SAFETY = "failed_safety"
FAILED_MODEL_REQUEST = "failed_model_request"
FAILED_UNKNOWN = "failed_unknown"

FINAL_STATUSES = {
    COMPLETED_ELIGIBLE,
    COMPLETED_NEEDS_REVIEW,
    FAILED_REDACTION,
    FAILED_SCHEMA,
    FAILED_GROUNDING,
    FAILED_SAFETY,
    FAILED_MODEL_REQUEST,
    FAILED_UNKNOWN,
}


@dataclass
class BatchStateStore:
    path: Path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"documents": {}}
        return read_json(self.path)

    def initialize(self, records: list[dict], resume: bool = False) -> dict[str, Any]:
        state = self.load() if resume else {"documents": {}}
        docs = state.setdefault("documents", {})
        for record in records:
            doc_id = record["document_id"]
            docs.setdefault(doc_id, {"document_id": doc_id, "domain": record["folder_domain"], "status": PENDING})
        self.save(state)
        return state

    def save(self, state: dict[str, Any]) -> None:
        write_json(self.path, state)

    def mark(self, document_id: str, status: str, **extra: Any) -> None:
        state = self.load()
        docs = state.setdefault("documents", {})
        current = docs.setdefault(document_id, {"document_id": document_id})
        current.update({"status": status, **extra})
        self.save(state)

    def is_final(self, document_id: str) -> bool:
        state = self.load()
        return state.get("documents", {}).get(document_id, {}).get("status") in FINAL_STATUSES
