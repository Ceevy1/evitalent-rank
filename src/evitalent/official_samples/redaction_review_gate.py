from __future__ import annotations

from datetime import datetime, timezone

from evitalent.official_samples.private_manifest import read_json, write_json
from evitalent.official_samples.settings import OfficialSampleSettings


class RedactionReviewGateError(RuntimeError):
    pass


def load_redaction_pilot_summary(settings: OfficialSampleSettings) -> list[dict]:
    if not settings.redaction_pilot_safe_summary_path.exists():
        raise RedactionReviewGateError("Redaction pilot summary does not exist.")
    payload = read_json(settings.redaction_pilot_safe_summary_path)
    return list(payload.get("documents", payload if isinstance(payload, list) else []))


def can_confirm_redaction_review(settings: OfficialSampleSettings) -> tuple[bool, list[str]]:
    errors: list[str] = []
    rows = load_redaction_pilot_summary(settings)
    by_domain = {row.get("domain"): row for row in rows}
    for domain in settings.domains:
        row = by_domain.get(domain)
        if not row:
            errors.append(f"{domain}: missing pilot redaction result")
            continue
        path = settings.redacted_pilot_dir / domain / f"{row['document_id']}.txt"
        if not path.exists():
            errors.append(f"{domain}: redacted text missing")
        if row.get("safety_passed") is not True:
            errors.append(f"{domain}: safety check failed")
    return not errors, errors


def confirm_redaction_review(settings: OfficialSampleSettings) -> dict:
    ok, errors = can_confirm_redaction_review(settings)
    if not ok:
        raise RedactionReviewGateError("; ".join(errors))
    payload = {
        "review_required": True,
        "review_confirmed": True,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "domains_confirmed": settings.domains,
        "allow_llm_pilot": True,
    }
    write_json(settings.review_gate_path, payload)
    return payload


def assert_llm_pilot_allowed(settings: OfficialSampleSettings) -> None:
    if not settings.review_gate_path.exists():
        raise RedactionReviewGateError("Redaction review gate is missing. Please review pilot redacted text first.")
    payload = read_json(settings.review_gate_path)
    if payload.get("review_confirmed") is not True or payload.get("allow_llm_pilot") is not True:
        raise RedactionReviewGateError("Redaction review has not been confirmed.")
