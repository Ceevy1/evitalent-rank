from __future__ import annotations

import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import ECOMMERCE_MULTI_ACHIEVEMENT_TEXT, EXPECTED_EVENTS, HR_MULTI_ACHIEVEMENT_TEXT, PRODUCTION_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline


SAMPLES = {
    "hr": HR_MULTI_ACHIEVEMENT_TEXT,
    "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
    "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
}


def main() -> None:
    recalls = []
    numeric_matches = []
    norm_matches = []
    grounding_rates = []
    schema_rates = []
    latencies = []
    for domain, text in SAMPLES.items():
        result = HybridExtractionPipeline().extract(text, f"doc_eval_{domain}", f"candidate_eval_{domain}")
        expected = EXPECTED_EVENTS[domain]
        actual = [(event.event_type, event.direction, event.metric_value) for event in result.normalized_events]
        event_recall = min(len(actual), len(expected)) / len(expected)
        numeric_exact = sum(1 for a, e in zip(actual, expected) if a[2] == e[2]) / len(expected)
        normalization_accuracy = sum(1 for a, e in zip(actual, expected) if a[0] == e[0] and a[1] == e[1]) / len(expected)
        grounding_pass_rate = sum(1 for event in result.normalized_events if event.grounding_status == "passed") / len(expected)
        schema_valid = 1.0 if result.candidate_extraction else 0.0
        recalls.append(event_recall)
        numeric_matches.append(numeric_exact)
        norm_matches.append(normalization_accuracy)
        grounding_rates.append(grounding_pass_rate)
        schema_rates.append(schema_valid)
        latencies.append(result.latency_seconds)
        print(f"{domain}: expected={len(expected)} actual={len(actual)} event_recall={event_recall:.2f} numeric_exact_match={numeric_exact:.2f} normalization_accuracy={normalization_accuracy:.2f} grounding_pass_rate={grounding_pass_rate:.2f}")
    print(f"event_recall={mean(recalls):.2f}")
    print(f"numeric_exact_match={mean(numeric_matches):.2f}")
    print(f"normalization_accuracy={mean(norm_matches):.2f}")
    print(f"grounding_pass_rate={mean(grounding_rates):.2f}")
    print(f"schema_valid_rate={mean(schema_rates):.2f}")
    print(f"average_latency_seconds={mean(latencies):.4f}")


if __name__ == "__main__":
    main()
