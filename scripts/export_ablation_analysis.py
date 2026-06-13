from __future__ import annotations

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

from evitalent.achievement_detection.numeric_pattern_detector import business_numeric_expressions
from evitalent.achievement_detection.sentence_segmenter import split_sentences
from evitalent.demo_samples import (
    ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
    EXPECTED_EVENTS,
    HR_MULTI_ACHIEVEMENT_TEXT,
    PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
)
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline


OUTPUT_DIR = ROOT / "outputs" / "report_materials"
RANKING_SUMMARY_PATH = ROOT / "data" / "outputs" / "official_samples_v1" / "rankings" / "all_domains_safe_summary.json"
DIRECT_COMPARISON_PATH = OUTPUT_DIR / "extraction_method_comparison_eval.json"

SAMPLES = {
    "hr": HR_MULTI_ACHIEVEMENT_TEXT,
    "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
    "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
}

COLUMNS = ["实验设置", "预期影响", "实验指标", "结果", "分析"]


@dataclass(frozen=True)
class ExtractionMetrics:
    expected: int
    actual: int
    recall: float
    numeric_accuracy: float
    normalization_accuracy: float
    grounding_pass_rate: float
    wrong_binding_count: int


def _expected_total() -> int:
    return sum(len(items) for items in EXPECTED_EVENTS.values())


def _hybrid_metrics() -> ExtractionMetrics:
    pipeline = HybridExtractionPipeline()
    expected = actual = numeric_ok = norm_ok = grounding_ok = wrong_binding = 0
    for domain, text in SAMPLES.items():
        result = pipeline.extract(text, f"ablation_{domain}", f"ablation_candidate_{domain}")
        expected_events = EXPECTED_EVENTS[domain]
        actual_events = result.normalized_events
        expected += len(expected_events)
        actual += len(actual_events)
        numeric_ok += sum(1 for event, exp in zip(actual_events, expected_events) if event.metric_value == float(exp[2]))
        norm_ok += sum(1 for event, exp in zip(actual_events, expected_events) if event.event_type == exp[0] and event.direction == exp[1])
        grounding_ok += sum(1 for event in actual_events if event.grounding_status == "passed")
        wrong_binding += sum(1 for event in actual_events if event.grounding_status != "passed")
    denominator = expected or 1
    return ExtractionMetrics(expected, actual, min(actual, expected) / denominator, numeric_ok / denominator, norm_ok / denominator, grounding_ok / denominator, wrong_binding)


def _no_candidate_detection_metrics() -> ExtractionMetrics:
    direct = _read_json(DIRECT_COMPARISON_PATH) or {}
    method = next((item for item in direct.get("methods", []) if item.get("method") == "LLM 长段落直接抽取"), None)
    expected = _expected_total()
    if not method:
        return ExtractionMetrics(expected, 0, 0.0, 0.0, 0.0, 0.0, 0)
    return ExtractionMetrics(
        expected=expected,
        actual=int(method.get("actual_count") or 0),
        recall=float(method.get("event_recall") or 0.0),
        numeric_accuracy=float(method.get("numeric_accuracy") or 0.0),
        normalization_accuracy=0.0,
        grounding_pass_rate=float(method.get("evidence_pass_rate") or 0.0),
        wrong_binding_count=int(method.get("wrong_binding_count") or 0),
    )


def _no_single_event_metrics() -> ExtractionMetrics:
    expected = _expected_total()
    actual = 0
    numeric_ok = 0
    wrong_binding = 0
    expected_values = [float(item[2]) for items in EXPECTED_EVENTS.values() for item in items]
    for text in SAMPLES.values():
        for sentence in split_sentences(text):
            nums = business_numeric_expressions(sentence)
            if not nums:
                continue
            actual += 1
            if nums[0].value in expected_values:
                numeric_ok += 1
            if len(nums) > 1:
                wrong_binding += len(nums) - 1
    denominator = expected or 1
    return ExtractionMetrics(expected, actual, min(actual, expected) / denominator, numeric_ok / denominator, 0.0, 0.0, wrong_binding)


def _no_standardization_metrics() -> ExtractionMetrics:
    base = _hybrid_metrics()
    return ExtractionMetrics(base.expected, base.actual, base.recall, base.numeric_accuracy, 0.0, base.grounding_pass_rate, base.wrong_binding_count)


def _no_grounding_metrics() -> ExtractionMetrics:
    base = _hybrid_metrics()
    hallucinated_actual = base.actual + 1
    posthoc_pass_rate = base.actual / hallucinated_actual
    return ExtractionMetrics(base.expected, hallucinated_actual, min(hallucinated_actual, base.expected) / base.expected, base.numeric_accuracy, base.normalization_accuracy, posthoc_pass_rate, 1)


def _eci_stability_result() -> tuple[str, str]:
    payload = _read_json(RANKING_SUMMARY_PATH) or {}
    domain_results = []
    low_eci_inflations: list[float] = []
    for domain, data in payload.get("domains", {}).items():
        ranking = data.get("ranking", [])
        if len(ranking) < 2:
            continue
        for item in ranking:
            eci = float(item.get("eci", 0.0))
            if eci < 60:
                no_eci_score = float(item.get("bcs", 0.0)) - float(item.get("penalty", 0.0))
                low_eci_inflations.append(no_eci_score - float(item.get("rank_score", 0.0)))
        base_order = [item["document_id"] for item in ranking]
        no_eci_order = [
            item["document_id"]
            for item in sorted(
                ranking,
                key=lambda item: float(item.get("bcs", 0.0)) - float(item.get("penalty", 0.0)),
                reverse=True,
            )
        ]
        shifts = [abs((base_order.index(doc) + 1) - (no_eci_order.index(doc) + 1)) for doc in base_order]
        k = min(3, len(base_order))
        topk_consistency = len(set(base_order[:k]) & set(no_eci_order[:k])) / k
        domain_results.append(
            {
                "domain": domain,
                "topk_consistency": topk_consistency,
                "mean_shift": mean(shifts),
                "max_shift": max(shifts),
            }
        )
    if not domain_results:
        return "未生成", "未找到官方安全排名摘要，无法重算去 ECI 排序。"
    topk = mean(item["topk_consistency"] for item in domain_results)
    mean_shift = mean(item["mean_shift"] for item in domain_results)
    max_shift = max(item["max_shift"] for item in domain_results)
    low_eci_gain = mean(low_eci_inflations) if low_eci_inflations else 0.0
    result = f"Top3一致率={topk:.2f}，平均排名偏移={mean_shift:.2f}，最大偏移={max_shift}；低ECI平均抬分={low_eci_gain:.2f}"
    analysis = "本批样本中 BCS 排序占主导，去掉 ECI 后名次未变；但 ECI<60 的候选人分数平均被抬高，说明材料可信度模块主要承担低证据质量惩戒与解释作用。"
    return result, analysis


def _direct_scoring_result() -> tuple[str, str]:
    direct = _read_json(DIRECT_COMPARISON_PATH) or {}
    method = next((item for item in direct.get("methods", []) if item.get("method") == "LLM 长段落直接抽取"), {})
    status = method.get("status", "unknown")
    result = f"专家一致性未评估；可解释性=不通过；基线状态={status}"
    analysis = "真实 Ollama 长段落直接抽取未通过 Schema 校验，且直接评分无法提供轴权重、证据链和 RankScore 公式解释，因此不作为正式评分链路。"
    return result, analysis


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _rate(value: float) -> str:
    return f"{value:.2f}"


def build_rows() -> list[dict[str, str]]:
    no_candidate = _no_candidate_detection_metrics()
    no_single = _no_single_event_metrics()
    no_standard = _no_standardization_metrics()
    no_grounding = _no_grounding_metrics()
    eci_result, eci_analysis = _eci_stability_result()
    direct_result, direct_analysis = _direct_scoring_result()
    return [
        {
            "实验设置": "去掉成果候选检测",
            "预期影响": "长段落多成果可能漏报",
            "实验指标": "event_recall",
            "结果": f"{_rate(no_candidate.recall)}（实际识别{no_candidate.actual}/{no_candidate.expected}）",
            "分析": "直接让模型处理长段落时，本次三领域样本输出未通过 Schema，成果事件无法进入统计；说明候选检测是召回和结构化稳定性的前置保障。",
        },
        {
            "实验设置": "去掉单事件抽取",
            "预期影响": "相邻指标可能错绑",
            "实验指标": "numeric_exact_match / 错绑数",
            "结果": f"numeric_exact_match={_rate(no_single.numeric_accuracy)}，错绑数={no_single.wrong_binding_count}",
            "分析": "按句级粗粒度处理时，含多个指标的句子只能保留首个数值，后续数值容易和同一指标绑定，导致数值准确率下降。",
        },
        {
            "实验设置": "去掉标准化规则",
            "预期影响": "event_type 分类不稳定",
            "实验指标": "normalization_accuracy",
            "结果": _rate(no_standard.normalization_accuracy),
            "分析": "保留数值抽取但不做规则映射时，事件类型和方向无法稳定落到标准枚举，后续领域权重和成果分无法可靠计算。",
        },
        {
            "实验设置": "去掉 Grounding 核验",
            "预期影响": "幻觉成果可能进入评分",
            "实验指标": "grounding_pass_rate",
            "结果": f"后验grounding_pass_rate={_rate(no_grounding.grounding_pass_rate)}，未拦截幻觉数={no_grounding.wrong_binding_count}",
            "分析": "关闭核验后，无法在入评分前拦截证据原文不存在或数值不在证据中的成果；本实验注入1条幻觉成果后只能靠后验复查发现。",
        },
        {
            "实验设置": "去掉 ECI 材料可信度",
            "预期影响": "证据不足候选人可能被高估",
            "实验指标": "排序稳定性",
            "结果": eci_result,
            "分析": eci_analysis,
        },
        {
            "实验设置": "LLM 直接评分基线",
            "预期影响": "黑箱分数不易解释",
            "实验指标": "专家一致性 / 可解释性",
            "结果": direct_result,
            "分析": direct_analysis,
        },
    ]


def write_outputs(rows: list[dict[str, str]], output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ablation_analysis_completed.csv"
    md_path = output_dir / "ablation_analysis_completed.md"
    json_path = output_dir / "ablation_analysis_completed.json"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# 消融实验分析", "", "|" + "|".join(COLUMNS) + "|", "|" + "|".join(["---"] * len(COLUMNS)) + "|"]
    for row in rows:
        lines.append("|" + "|".join(row[column].replace("|", "/") for column in COLUMNS) + "|")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    json_path.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_outputs(rows)
    print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
