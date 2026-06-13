from __future__ import annotations

from fastapi import APIRouter

from evitalent.api.schemas import ManualReviewRequest
from evitalent.official_samples.manual_review_store import ManualReviewStore
from evitalent.official_samples.private_manifest import read_json
from evitalent.official_samples.settings import load_official_sample_settings

router = APIRouter(prefix="/api/v1/official-samples", tags=["official-samples"])


def _read_if_exists(path):
    return read_json(path) if path.exists() else None


@router.get("/status")
def official_samples_status() -> dict:
    settings = load_official_sample_settings(create_dirs=False)
    manual_review_store = ManualReviewStore(settings.manual_review_path)
    return {
        "inventory": _read_if_exists(settings.inventory_safe_summary_path),
        "redaction_pilot": _read_if_exists(settings.redaction_pilot_safe_summary_path),
        "review_gate_confirmed": bool(settings.review_gate_path.exists() and read_json(settings.review_gate_path).get("review_confirmed") is True),
        "llm_pilot": _read_if_exists(settings.llm_pilot_safe_summary_path),
        "batch": _read_if_exists(settings.batch_output_dir / "safe_processing_summary.json"),
        "manual_review": manual_review_store.load(),
        "manual_review_summary": manual_review_store.summary(),
        "rankings": _read_if_exists(settings.rankings_dir / "all_domains_safe_summary.json"),
        "safety_notice": "系统默认仅处理脱敏后的简历文本，排名结果用于比赛分析与辅助评价，不构成最终录用结论。",
    }


@router.post("/manual-review")
def record_manual_review(request: ManualReviewRequest) -> dict:
    settings = load_official_sample_settings(create_dirs=True)
    store = ManualReviewStore(settings.manual_review_path)
    review = store.record(
        request.document_id,
        domain=request.domain,
        source_status=request.source_status,
        decision=request.decision,
        reviewer=request.reviewer,
        note=request.note,
    )
    return {"review": review, "summary": store.summary()}
