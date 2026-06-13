from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import ECOMMERCE_MULTI_ACHIEVEMENT_TEXT, HR_MULTI_ACHIEVEMENT_TEXT, PRODUCTION_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline


OUTPUT_DIR = ROOT / "outputs" / "report_materials"

DOMAIN_LABELS = {
    "brand": "品牌",
    "ecommerce": "电商",
    "hr": "人力资源",
    "production": "生产",
    "rd": "研发",
    "sales": "销售",
}

COLUMNS = ["领域", "应识别成果数", "实际识别成果数", "事件召回率", "数值准确率", "单位准确率", "标准化准确率", "Grounding 通过率"]


@dataclass(frozen=True)
class ExpectedEvent:
    event_type: str
    direction: str
    metric_value: float | None
    unit: str | None


SAMPLES: dict[str, str] = {
    "brand": (
        "某候选人负责品牌管理和新品上市。"
        "6个月新品上市3个，品牌销售额增长18%，ROI达到1.8。"
    ),
    "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
    "hr": HR_MULTI_ACHIEVEMENT_TEXT,
    "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
    "rd": (
        "某候选人负责研发项目和技术转化。"
        "14个月新品上市5个，获得专利2项，技术转化收入达到300万元。"
    ),
    "sales": (
        "某候选人负责区域销售和渠道拓展。"
        "年销售额达到9500万元，回款率达到96%，新增客户24家。"
    ),
}

EXPECTED_EVENTS: dict[str, list[ExpectedEvent]] = {
    "brand": [
        ExpectedEvent("product_launch", "achieved_amount", 3.0, "count"),
        ExpectedEvent("revenue_growth", "increase_by", 18.0, "percent"),
        ExpectedEvent("roi_improvement", "achieved_level", 1.8, "ratio"),
    ],
    "ecommerce": [
        ExpectedEvent("gmv_growth", "achieved_level", 1.0, "CNY"),
        ExpectedEvent("conversion_improvement", "achieved_level", 12.0, "percent"),
        ExpectedEvent("roi_improvement", "achieved_level", 1.5, "ratio"),
    ],
    "hr": [
        ExpectedEvent("recruitment_delivery", "achieved_amount", 120.0, "person"),
        ExpectedEvent("recruitment_completion_rate", "achieved_level", 88.0, "percent"),
        ExpectedEvent("recruitment_delivery", "achieved_amount", 18.0, "person"),
        ExpectedEvent("recruitment_completion_rate", "achieved_level", 91.0, "percent"),
        ExpectedEvent("retention_improvement", "decrease_by", 15.0, "percent"),
    ],
    "production": [
        ExpectedEvent("efficiency_improvement", "increase_by", 1.2, "percent"),
        ExpectedEvent("loss_reduction", "decrease_by", 0.6, "percent"),
        ExpectedEvent("automation_upgrade", "achieved_amount", 2.0, "count"),
        ExpectedEvent("quality_improvement", "maintained", 0.0, None),
    ],
    "rd": [
        ExpectedEvent("product_launch", "achieved_amount", 5.0, "count"),
        ExpectedEvent("patent_publication", "achieved_amount", 2.0, "count"),
        ExpectedEvent("technology_transfer", "achieved_level", 300.0, "CNY"),
    ],
    "sales": [
        ExpectedEvent("revenue_growth", "achieved_level", 9500.0, "CNY"),
        ExpectedEvent("collection_performance", "achieved_level", 96.0, "percent"),
        ExpectedEvent("channel_expansion", "achieved_amount", 24.0, "count"),
    ],
}


def _value_equal(actual: float | None, expected: float | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return abs(float(actual) - float(expected)) <= 1e-9


def _rate(numerator: int | float, denominator: int) -> float:
    return round(float(numerator) / denominator, 4) if denominator else 0.0


def _row(domain: str, pipeline: HybridExtractionPipeline) -> tuple[dict[str, Any], dict[str, Any]]:
    result = pipeline.extract(SAMPLES[domain], f"six_domain_accuracy_{domain}", f"six_domain_candidate_{domain}")
    expected = EXPECTED_EVENTS[domain]
    actual = result.normalized_events
    compared = list(zip(actual, expected))
    denominator = len(expected)

    numeric_ok = sum(1 for event, exp in compared if _value_equal(event.metric_value, exp.metric_value))
    unit_ok = sum(1 for event, exp in compared if event.unit == exp.unit)
    normalization_ok = sum(1 for event, exp in compared if event.event_type == exp.event_type and event.direction == exp.direction)
    grounding_ok = sum(1 for event in actual if event.grounding_status == "passed")

    row = {
        "领域": DOMAIN_LABELS[domain],
        "应识别成果数": denominator,
        "实际识别成果数": len(actual),
        "事件召回率": _rate(min(len(actual), denominator), denominator),
        "数值准确率": _rate(numeric_ok, denominator),
        "单位准确率": _rate(unit_ok, denominator),
        "标准化准确率": _rate(normalization_ok, denominator),
        "Grounding 通过率": _rate(min(grounding_ok, denominator), denominator),
    }
    detail = {
        "domain": domain,
        "text": SAMPLES[domain],
        "expected": [event.__dict__ for event in expected],
        "actual": [
            {
                "event_type": event.event_type,
                "direction": event.direction,
                "metric_value": event.metric_value,
                "unit": event.unit,
                "grounding_status": event.grounding_status,
                "normalization_rule_id": event.normalization_rule_id,
                "evidence_quote": event.evidence_quote,
            }
            for event in actual
        ],
    }
    return row, detail


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pipeline = HybridExtractionPipeline()
    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for domain in ["brand", "ecommerce", "hr", "production", "sales", "rd"]:
        row, detail = _row(domain, pipeline)
        rows.append(row)
        details.append(detail)
    return rows, details


def write_outputs(rows: list[dict[str, Any]], details: list[dict[str, Any]], output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "six_domain_extraction_accuracy.csv"
    md_path = output_dir / "six_domain_extraction_accuracy.md"
    json_path = output_dir / "six_domain_extraction_accuracy.json"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 六领域成果抽取与标准化准确性实验",
        "",
        "说明：本实验使用六领域受控匿名样本文本；前三领域沿用项目既有 fixture，品牌/销售/研发补充同口径成果样本。标准化准确率同时要求 event_type 与 direction 匹配。",
        "",
        "|" + "|".join(COLUMNS) + "|",
        "|" + "|".join(["---"] * len(COLUMNS)) + "|",
    ]
    for row in rows:
        lines.append("|" + "|".join(str(row[column]).replace("|", "/") for column in COLUMNS) + "|")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_path.write_text(
        json.dumps(
            {
                "metric_definition": {
                    "事件召回率": "min(实际识别成果数, 应识别成果数) / 应识别成果数",
                    "数值准确率": "按成果顺序比较 metric_value 完全匹配比例",
                    "单位准确率": "按成果顺序比较标准单位完全匹配比例",
                    "标准化准确率": "按成果顺序比较 event_type 与 direction 同时匹配比例",
                    "Grounding 通过率": "grounding_status=passed 的成果数 / 应识别成果数",
                },
                "rows": rows,
                "details": details,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    rows, details = build_rows()
    write_outputs(rows, details)
    print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
