from __future__ import annotations

from evitalent.privacy.redactor import redact_text


def compare_redacted_counterfactual_inputs(text_a: str, text_b: str) -> dict:
    """Optional research helper for fictitious or explicitly authorized text only."""
    redacted_a = redact_text(text_a).redacted_text
    redacted_b = redact_text(text_b).redacted_text
    return {
        "redacted_inputs_identical": redacted_a == redacted_b,
        "length_delta": abs(len(redacted_a) - len(redacted_b)),
        "safe_for_llm_bias_probe": redacted_a == redacted_b,
    }
