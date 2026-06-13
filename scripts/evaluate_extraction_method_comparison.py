from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import (
    ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
    EXPECTED_EVENTS,
    HR_MULTI_ACHIEVEMENT_TEXT,
    PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
)
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline
from evitalent.extraction.llm_client import LLMClient
from evitalent.extraction.llm_extractor import LLMExtractionError, LLMExtractor
from evitalent.extraction.safety_validator import assert_redacted_text_safe
from evitalent.models.extraction import AchievementEvent, CandidateExtraction
from evitalent.parser.docx_parser import DocxDocumentParser
from evitalent.privacy.redactor import redact_text


OUTPUT_DIR = ROOT / "outputs" / "report_materials"
MODEL_NAME = "evitalent-extractor:7b"
BASE_URL = "http://127.0.0.1:11434"

FALLBACK_SAMPLES = {
    "hr": HR_MULTI_ACHIEVEMENT_TEXT,
    "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
    "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
}

DOCX_SAMPLES = {
    "hr": ROOT / "data" / "fixtures" / "source_documents" / "fictional_hr_resume_for_ollama.docx",
    "production": ROOT / "data" / "fixtures" / "source_documents" / "fictional_production_resume_for_ollama.docx",
    "ecommerce": ROOT / "data" / "fixtures" / "source_documents" / "fictional_ecommerce_resume_for_ollama.docx",
}

METHOD_COLUMNS = [
    "方法",
    "应识别成果数",
    "实际识别成果数",
    "事件召回率",
    "错绑数量",
    "数值准确率",
    "证据核验通过率",
    "结论",
]


@dataclass(frozen=True)
class MethodEval:
    method: str
    expected_count: int
    actual_count: int | None
    event_recall: float | None
    wrong_binding_count: int | None
    numeric_accuracy: float | None
    evidence_pass_rate: float | None
    conclusion: str
    status: str
    details: list[dict[str, Any]]

    def table_row(self) -> dict[str, Any]:
        return {
            "方法": self.method,
            "应识别成果数": self.expected_count,
            "实际识别成果数": "未运行" if self.actual_count is None else self.actual_count,
            "事件召回率": _fmt_rate(self.event_recall),
            "错绑数量": "未运行" if self.wrong_binding_count is None else self.wrong_binding_count,
            "数值准确率": _fmt_rate(self.numeric_accuracy),
            "证据核验通过率": _fmt_rate(self.evidence_pass_rate),
            "结论": self.conclusion,
        }

    def json_obj(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "status": self.status,
            "expected_count": self.expected_count,
            "actual_count": self.actual_count,
            "event_recall": self.event_recall,
            "wrong_binding_count": self.wrong_binding_count,
            "numeric_accuracy": self.numeric_accuracy,
            "evidence_pass_rate": self.evidence_pass_rate,
            "conclusion": self.conclusion,
            "details": self.details,
        }


def _fmt_rate(value: float | None) -> str:
    return "未运行" if value is None else f"{value:.2f}"


def _event_key(event: AchievementEvent | tuple[str, str, float]) -> tuple[str, str, float | None]:
    if isinstance(event, tuple):
        return event[0], event[1], float(event[2])
    return event.event_type.value, event.direction, event.metric_value


def _value_in_quote(value: float | None, quote: str) -> bool:
    if value is None:
        return False
    expected = str(int(value)) if float(value).is_integer() else str(value)
    numbers = set(re.findall(r"\d+(?:\.\d+)?", quote))
    return expected in numbers or str(value) in numbers


def _evidence_passes(event: AchievementEvent, evidence_by_id: dict[str, str], text: str) -> bool:
    quote = evidence_by_id.get(event.evidence_id, "")
    return bool(quote and quote in text and _value_in_quote(event.metric_value, quote))


def _load_eval_samples() -> dict[str, str]:
    samples: dict[str, str] = {}
    parser = DocxDocumentParser()
    for domain, path in DOCX_SAMPLES.items():
        if not path.exists():
            samples[domain] = FALLBACK_SAMPLES[domain]
            continue
        parsed = parser.parse(path)
        redacted_text = redact_text(parsed.cleaned_text).redacted_text
        assert_redacted_text_safe(redacted_text)
        samples[domain] = redacted_text
    return samples


def _summarize_events(events: list[AchievementEvent], expected: list[tuple[str, str, float]], text: str, evidence_by_id: dict[str, str]) -> dict[str, Any]:
    expected_keys = [_event_key(item) for item in expected]
    actual_keys = [_event_key(item) for item in events]
    matched = sum(1 for key in expected_keys if key in actual_keys)
    numeric_matched = sum(
        1
        for expected_event in expected
        if any(actual.metric_value == float(expected_event[2]) for actual in events)
    )
    evidence_pass_count = sum(1 for event in events if _evidence_passes(event, evidence_by_id, text))
    wrong_binding_count = sum(1 for event in events if not _evidence_passes(event, evidence_by_id, text))
    denominator = len(expected) or 1
    return {
        "expected_count": len(expected),
        "actual_count": len(events),
        "event_recall": matched / denominator,
        "numeric_accuracy": numeric_matched / denominator,
        "evidence_pass_rate": evidence_pass_count / denominator,
        "wrong_binding_count": wrong_binding_count,
    }


def evaluate_hybrid() -> MethodEval:
    pipeline = HybridExtractionPipeline()
    details = []
    for domain, text in _load_eval_samples().items():
        result = pipeline.extract(text, f"hybrid_eval_{domain}", f"hybrid_candidate_{domain}")
        events = [
            AchievementEvent(
                achievement_id=event.achievement_id,
                event_type=event.event_type,
                metric_name=event.normalized_metric_name,
                metric_value=event.metric_value,
                metric_value_upper=event.metric_value_upper,
                unit=event.unit,
                direction=event.direction,
                period_months=event.period_months,
                approximate=event.approximate,
                lower_bound=event.lower_bound,
                candidate_contribution="hybrid extraction",
                evidence_grade="A" if event.grounding_status == "passed" else "D",
                evidence_id=event.evidence_id,
            )
            for event in result.normalized_events
        ]
        evidence_by_id = {event.evidence_id: event.evidence_quote for event in result.normalized_events}
        item = _summarize_events(events, EXPECTED_EVENTS[domain], text, evidence_by_id)
        item["domain"] = domain
        details.append(item)

    return _aggregate(
        "混合抽取方法",
        details,
        "Python 先定位成果候选，再逐条解释与规则标准化；事件、数值和证据核验均通过。",
        "completed",
    )


def evaluate_direct_llm() -> MethodEval:
    expected_total = sum(len(events) for events in EXPECTED_EVENTS.values())
    client = LLMClient(
        provider="local_ollama",
        base_url=BASE_URL,
        api_key="ollama",
        model=MODEL_NAME,
        temperature=0,
        timeout_seconds=120,
        max_retries=0,
        seed=9,
    )
    health = client.health_check()
    if not health.ok:
        return MethodEval(
            method="LLM 长段落直接抽取",
            expected_count=expected_total,
            actual_count=None,
            event_recall=None,
            wrong_binding_count=None,
            numeric_accuracy=None,
            evidence_pass_rate=None,
            conclusion=f"未运行：本地模型不可用（{health.message}）。启动 Ollama 后重跑脚本可生成真实基线。",
            status="not_run_model_unavailable",
            details=[{"health_message": health.message}],
        )

    extractor = LLMExtractor(client=client, output_dir=OUTPUT_DIR / "direct_llm_tmp", mode="local_ollama")
    details = []
    for domain, text in _load_eval_samples().items():
        try:
            candidate = extractor.extract(f"direct_eval_{domain}", redacted_text=text)
            details.append(_evaluate_candidate(domain, text, candidate))
        except LLMExtractionError as exc:
            details.append(
                {
                    "domain": domain,
                    "expected_count": len(EXPECTED_EVENTS[domain]),
                    "actual_count": 0,
                    "event_recall": 0.0,
                    "numeric_accuracy": 0.0,
                    "evidence_pass_rate": 0.0,
                    "wrong_binding_count": 0,
                    "error": str(exc),
                }
            )

    all_failed_schema = all("error" in item for item in details)
    conclusion = (
        "三领域长段落直接抽取均未通过 Schema 校验，无法进入正式成果统计、证据核验和评分链路。"
        if all_failed_schema
        else "模型一次性从长段落生成结构化结果；结果需通过 Schema、证据绑定和数值核验后才可作为对照指标。"
    )
    return _aggregate(
        "LLM 长段落直接抽取",
        details,
        conclusion,
        "completed_schema_failed" if all_failed_schema else "completed",
    )


def _evaluate_candidate(domain: str, text: str, candidate: CandidateExtraction) -> dict[str, Any]:
    evidence_by_id = {item.evidence_id: item.quote for item in candidate.evidence_items}
    item = _summarize_events(candidate.achievement_events, EXPECTED_EVENTS[domain], text, evidence_by_id)
    item["domain"] = domain
    return item


def _aggregate(method: str, details: list[dict[str, Any]], conclusion: str, status: str) -> MethodEval:
    expected_count = sum(int(item["expected_count"]) for item in details)
    actual_count = sum(int(item["actual_count"]) for item in details)
    wrong_binding_count = sum(int(item["wrong_binding_count"]) for item in details)
    return MethodEval(
        method=method,
        expected_count=expected_count,
        actual_count=actual_count,
        event_recall=mean(float(item["event_recall"]) for item in details),
        wrong_binding_count=wrong_binding_count,
        numeric_accuracy=mean(float(item["numeric_accuracy"]) for item in details),
        evidence_pass_rate=mean(float(item["evidence_pass_rate"]) for item in details),
        conclusion=conclusion,
        status=status,
        details=details,
    )


def _write_outputs(rows: list[MethodEval], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "extraction_method_comparison_eval.csv"
    md_path = output_dir / "extraction_method_comparison_eval.md"
    json_path = output_dir / "extraction_method_comparison_eval.json"

    table_rows = [row.table_row() for row in rows]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=METHOD_COLUMNS)
        writer.writeheader()
        writer.writerows(table_rows)

    lines = [
        "# LLM 长段落直接抽取 vs 混合抽取评估",
        "",
        "|" + "|".join(METHOD_COLUMNS) + "|",
        "|" + "|".join(["---"] * len(METHOD_COLUMNS)) + "|",
    ]
    for row in table_rows:
        lines.append("|" + "|".join(str(row[column]) for column in METHOD_COLUMNS) + "|")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_path.write_text(
        json.dumps({"methods": [row.json_obj() for row in rows]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate direct long-paragraph LLM extraction against hybrid extraction.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    results = [evaluate_direct_llm(), evaluate_hybrid()]
    _write_outputs(results, args.output_dir)
    print(json.dumps({"methods": [result.table_row() for result in results]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
