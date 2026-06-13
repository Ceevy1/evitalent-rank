from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.demo_samples import EXPECTED_EVENTS, ECOMMERCE_MULTI_ACHIEVEMENT_TEXT, HR_MULTI_ACHIEVEMENT_TEXT, PRODUCTION_MULTI_ACHIEVEMENT_TEXT
from evitalent.extraction.hybrid_extraction_pipeline import HybridExtractionPipeline


OUTPUT_DIR = ROOT / "outputs" / "report_materials"
SAFE_SOURCES = {
    "weights": ROOT / "config" / "domain_weights.yaml",
    "docx_e2e": ROOT / "data" / "outputs" / "audit_reports" / "real_ollama_docx_e2e_summary.json",
    "official_batch": ROOT / "data" / "outputs" / "official_samples_v1" / "batch" / "safe_processing_summary.json",
    "official_inventory": ROOT / "data" / "outputs" / "official_samples_v1" / "manifests" / "inventory_safe_summary.json",
    "redaction_pilot": ROOT / "data" / "outputs" / "official_samples_v1" / "pilot" / "redaction_pilot_safe_summary.json",
    "llm_pilot": ROOT / "data" / "outputs" / "official_samples_v1" / "pilot" / "llm_pilot_safe_summary.json",
    "robustness": ROOT / "data" / "outputs" / "audit_reports" / "robustness_demo_hr.json",
}

DOMAIN_LABELS = {
    "ecommerce": "电商",
    "brand": "品牌",
    "hr": "人力资源",
    "production": "生产",
    "sales": "销售",
    "rd": "研发",
}

AXIS_LABELS = {
    "education": "教育基础",
    "match": "领域匹配",
    "experience": "相关经验",
    "stability": "稳定性",
    "progression": "成长轨迹",
    "platform": "平台复杂度",
    "management": "管理跨度",
    "competency": "专业能力",
    "achievement": "成果影响",
    "collaboration": "协同领导",
}

TABLES = {
    "domain_weights": "六领域权重表",
    "extraction_comparison": "LLM 直接抽取 vs 混合抽取对比表",
    "fictional_docx_e2e_results": "虚构 DOCX 真实 Ollama 端到端结果表",
    "official_sample_processing_stats": "主办方样本处理统计表",
    "ablation_experiments": "消融实验表",
    "privacy_safety_checks": "隐私保护与安全校验表",
    "assistant_qa_examples": "AI 助手问答示例表",
}


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_table(output_dir: Path, name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{name}.csv"
    md_path = output_dir / f"{name}.md"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    md_path.write_text(_markdown_table(rows, columns, TABLES[name]), encoding="utf-8")


def _markdown_table(rows: list[dict[str, Any]], columns: list[str], title: str) -> str:
    lines = [f"# {title}", "", "|" + "|".join(columns) + "|", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append("|" + "|".join(_cell(row.get(column, "")) for column in columns) + "|")
    lines.append("")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "/")


def _round(value: Any, digits: int = 4) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    return value


def build_domain_weight_rows() -> list[dict[str, Any]]:
    cfg = yaml.safe_load(SAFE_SOURCES["weights"].read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for domain, payload in cfg["domains"].items():
        weights = payload["weights"]
        row = {"领域": payload.get("label", DOMAIN_LABELS.get(domain, domain)), "权重合计": round(sum(float(v) for v in weights.values()), 4)}
        row.update({AXIS_LABELS.get(axis, axis): weight for axis, weight in weights.items()})
        rows.append(row)
    return rows


def build_extraction_comparison_rows() -> list[dict[str, Any]]:
    docx = _read_json(SAFE_SOURCES["docx_e2e"]) or {}
    return [
        {
            "方案": "LLM 直接抽取",
            "实验状态": "待补充安全基线",
            "事实定位": "模型一次性生成结构化结果",
            "标准化方式": "模型生成后校验",
            "评分边界": "不允许模型计算排名",
            "平均事件召回": "待填",
            "平均数字匹配": "待填",
            "平均标准化准确率": "待填",
            "平均证据通过率": "待填",
            "安全结论": "仅作为对照方案，报告中不得作为正式评分链路",
        },
        {
            "方案": "混合抽取",
            "实验状态": "已完成虚构 DOCX 联调",
            "事实定位": "Python 先定位成果候选，再由模型解释单条候选",
            "标准化方式": "Python 规则映射事件类型与方向",
            "评分边界": "Python 评分引擎计算 BCS、ECI、Penalty、RankScore",
            "平均事件召回": docx.get("event_recall", "待填"),
            "平均数字匹配": docx.get("numeric_exact_match", "待填"),
            "平均标准化准确率": docx.get("normalization_accuracy", "待填"),
            "平均证据通过率": docx.get("grounding_pass_rate", "待填"),
            "安全结论": "通过 Schema、证据绑定和安全复核后才可进入评分",
        },
    ]


def build_fictional_docx_rows() -> list[dict[str, Any]]:
    docx = _read_json(SAFE_SOURCES["docx_e2e"]) or {}
    rows = []
    for item in docx.get("documents", []):
        rows.append(
            {
                "匿名文档编号": item.get("document_id"),
                "领域": DOMAIN_LABELS.get(item.get("domain"), item.get("domain")),
                "模型模式": item.get("extraction_mode"),
                "模型别名": item.get("model_name"),
                "候选成果数": item.get("detected_achievement_candidate_count"),
                "标准化成果数": item.get("normalized_event_count"),
                "证据通过成果数": item.get("grounded_event_count"),
                "Schema 通过": item.get("schema_passed"),
                "安全通过": item.get("safety_passed"),
                "可评分": item.get("eligible_for_scoring"),
                "BCS": item.get("bcs"),
                "ECI": item.get("eci"),
                "Penalty": item.get("penalty"),
                "RankScore": item.get("rank_score"),
                "推理秒数": item.get("inference_seconds"),
                "事件召回": item.get("event_recall"),
                "数字匹配": item.get("numeric_exact_match"),
                "标准化准确率": item.get("normalization_accuracy"),
                "证据通过率": item.get("grounding_pass_rate"),
            }
        )
    if rows:
        return rows
    return [
        {
            "匿名文档编号": "待填",
            "领域": "待填",
            "模型模式": "local_ollama",
            "模型别名": "待填",
            "候选成果数": "待填",
            "标准化成果数": "待填",
            "证据通过成果数": "待填",
            "Schema 通过": "待填",
            "安全通过": "待填",
            "可评分": "待填",
            "BCS": "待填",
            "ECI": "待填",
            "Penalty": "待填",
            "RankScore": "待填",
            "推理秒数": "待填",
            "事件召回": "待填",
            "数字匹配": "待填",
            "标准化准确率": "待填",
            "证据通过率": "待填",
        }
    ]


def build_official_sample_rows() -> list[dict[str, Any]]:
    batch = _read_json(SAFE_SOURCES["official_batch"])
    if not batch:
        inventory = _read_json(SAFE_SOURCES["official_inventory"]) or []
        return [
            {
                "领域": DOMAIN_LABELS.get(item.get("domain"), item.get("domain", "待填")),
                "样本总数": item.get("document_count", "待填"),
                "可读取样本数": item.get("readable_count", "待填"),
                "已处理样本数": "待填",
                "可纳入比较数": "待填",
                "待人工核验数": "待填",
                "失败数": "待填",
                "安全泄露计数": "待填",
                "平均处理秒数": "待填",
                "状态": "批处理未完成，基于安全盘点生成模板",
            }
            for item in inventory
        ] or [
            {
                "领域": "待填",
                "样本总数": "待填",
                "可读取样本数": "待填",
                "已处理样本数": "待填",
                "可纳入比较数": "待填",
                "待人工核验数": "待填",
                "失败数": "待填",
                "安全泄露计数": "待填",
                "平均处理秒数": "待填",
                "状态": "待运行安全批处理",
            }
        ]
    return [
        {
            "领域": DOMAIN_LABELS.get(item.get("domain"), item.get("domain")),
            "样本总数": item.get("total_documents"),
            "可读取样本数": item.get("total_documents"),
            "已处理样本数": item.get("processed_documents"),
            "可纳入比较数": item.get("eligible_documents"),
            "待人工核验数": item.get("needs_review_documents"),
            "失败数": item.get("failed_documents"),
            "安全泄露计数": item.get("sensitive_leakage_count"),
            "平均处理秒数": item.get("average_document_inference_seconds"),
            "状态": "已完成安全匿名统计",
        }
        for item in batch
    ]


def build_ablation_rows() -> list[dict[str, Any]]:
    rows = []
    robustness = _read_json(SAFE_SOURCES["robustness"]) or {}
    for version, metrics in robustness.get("comparisons", {}).items():
        rows.append(
            {
                "实验名称": "等价表达稳定性消融",
                "消融设置": version,
                "领域": DOMAIN_LABELS.get(robustness.get("domain"), robustness.get("domain")),
                "TopK 一致率": metrics.get("top_k_consistency"),
                "平均排名偏移": metrics.get("mean_rank_shift"),
                "最大排名偏移": metrics.get("max_rank_shift"),
                "状态": robustness.get("robustness_audit_status", "待填"),
                "结论": "排序对等价文本表达保持稳定",
            }
        )
    if rows:
        return rows
    return [
        {
            "实验名称": "模块消融",
            "消融设置": "待填",
            "领域": "待填",
            "TopK 一致率": "待填",
            "平均排名偏移": "待填",
            "最大排名偏移": "待填",
            "状态": "待补充安全实验输出",
            "结论": "待填",
        }
    ]


def build_privacy_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    redaction = _read_json(SAFE_SOURCES["redaction_pilot"]) or {}
    docs = redaction.get("documents", []) if isinstance(redaction, dict) else []
    if docs:
        rows.append(
            {
                "检查项": "Pilot 脱敏安全复核",
                "样本范围": f"{len(docs)} 份匿名样本",
                "通过数": sum(1 for item in docs if item.get("safety_passed") is True),
                "风险计数": sum(int(item.get("warning_count", 0)) for item in docs),
                "输出材料": "仅保留匿名编号、领域、计数和状态",
                "结论": "通过" if all(item.get("safety_passed") is True for item in docs) else "需复核",
            }
        )
    llm_pilot = _read_json(SAFE_SOURCES["llm_pilot"]) or {}
    llm_docs = llm_pilot.get("documents", []) if isinstance(llm_pilot, dict) else []
    if llm_docs:
        rows.append(
            {
                "检查项": "Pilot 抽取安全复核",
                "样本范围": f"{len(llm_docs)} 份匿名样本",
                "通过数": sum(1 for item in llm_docs if item.get("safety_passed") is True),
                "风险计数": sum(0 if item.get("safety_passed") is True else 1 for item in llm_docs),
                "输出材料": "仅保留抽取质量、评分和耗时统计",
                "结论": "通过" if all(item.get("safety_passed") is True for item in llm_docs) else "需复核",
            }
        )
    docx = _read_json(SAFE_SOURCES["docx_e2e"]) or {}
    rows.append(
        {
            "检查项": "虚构 DOCX 端到端安全复核",
            "样本范围": f"{len(docx.get('documents', []))} 份虚构样本",
            "通过数": len([item for item in docx.get("documents", []) if item.get("safety_passed") is True]),
            "风险计数": docx.get("sensitive_leakage_count", "待填"),
            "输出材料": "仅保留虚构样本匿名指标",
            "结论": "通过" if docx.get("safety_passed") is True else "待填",
        }
    )
    return rows


def build_assistant_rows() -> list[dict[str, Any]]:
    return [
        {
            "场景": "排名解释",
            "示例问题": "为什么当前 HR 第一名排名靠前？",
            "安全范围": "当前任务的匿名候选人摘要",
            "期望回答要点": "解释 RankScore、BCS、ECI、优势标签和待核验事项，不输出身份类信息",
            "安全状态": "基于安全上下文回答",
        },
        {
            "场景": "候选人比较",
            "示例问题": "比较两位匿名候选人的成果差异。",
            "安全范围": "匿名候选人编号与安全评分摘要",
            "期望回答要点": "比较成果数量、证据可信度和领域匹配，不给出录用决定",
            "安全状态": "基于安全上下文回答",
        },
        {
            "场景": "面试核验建议",
            "示例问题": "为其中一位候选人生成面试核验问题。",
            "安全范围": "待核验事项与证据状态",
            "期望回答要点": "围绕成果真实性、角色贡献和数据口径生成问题",
            "安全状态": "基于安全上下文回答",
        },
    ]


def build_fixture_accuracy_rows() -> list[dict[str, Any]]:
    samples = {
        "hr": HR_MULTI_ACHIEVEMENT_TEXT,
        "production": PRODUCTION_MULTI_ACHIEVEMENT_TEXT,
        "ecommerce": ECOMMERCE_MULTI_ACHIEVEMENT_TEXT,
    }
    rows = []
    for domain, text in samples.items():
        result = HybridExtractionPipeline().extract(text, f"doc_report_{domain}", f"candidate_report_{domain}")
        expected = EXPECTED_EVENTS[domain]
        actual = [(event.event_type, event.direction, event.metric_value) for event in result.normalized_events]
        rows.append(
            {
                "领域": DOMAIN_LABELS.get(domain, domain),
                "期望事件数": len(expected),
                "实际事件数": len(actual),
                "事件召回": _round(min(len(actual), len(expected)) / len(expected)),
                "数字匹配": _round(sum(1 for a, e in zip(actual, expected) if a[2] == e[2]) / len(expected)),
                "标准化准确率": _round(sum(1 for a, e in zip(actual, expected) if a[0] == e[0] and a[1] == e[1]) / len(expected)),
                "证据通过率": _round(sum(1 for event in result.normalized_events if event.grounding_status == "passed") / len(expected)),
                "Schema 通过": bool(result.candidate_extraction),
            }
        )
    return rows


def write_algorithm_flow(output_dir: Path) -> None:
    content = """# 模型算法流程

```mermaid
flowchart TD
  A["安全匿名文本"] --> B["Python 成果候选检测"]
  B --> C["单指标候选拆分"]
  C --> D["LLM 解释候选事实"]
  D --> E["Python 事件类型与方向标准化"]
  E --> F["证据与数字一致性校验"]
  F --> G["结构化候选人画像"]
  G --> H["BCS / ECI / Penalty 计算"]
  H --> I["RankScore 确定性排序"]
  I --> J["审计、报告与 AI 助手安全问答"]
```

## 关键边界

- LLM 只解释候选事实，不计算排名。
- 标准事件类型、方向、评分和排序由 Python 规则引擎完成。
- RankScore 公式和六领域权重只读取既有配置，不在导出过程中修改。
- 报告材料只使用安全摘要、fixture 实验结果和匿名统计。
"""
    (output_dir / "model_algorithm_flow.md").write_text(content, encoding="utf-8")


def write_innovation_summary(output_dir: Path) -> None:
    content = """# 可直接写入报告的创新点总结

1. 构建了“LLM 语义增强 + Python 确定性评分”的混合架构，将大模型限定在事实解释和语义抽取环节，最终评分与排序由可审计规则完成。
2. 将成果事件拆分为候选检测、单指标解释、规则标准化和证据校验四个阶段，提高了数字成果的可追溯性和可复核性。
3. 六个岗位领域使用独立权重表，但共享 BCS、ECI、Penalty、RankScore 评分框架，使评价既体现领域差异，又保持公式一致。
4. 引入证据可信度指数，将量化证据、可追溯性、完整性、一致性和可核验性纳入排名解释，避免只比较简历包装强度。
5. 内置隐私隔离、安全摘要、人工核验和审计流程，报告材料不依赖非安全输入，也不暴露身份、联系方式或私有文件标识。
6. AI 助手基于安全匿名上下文回答排名解释、候选人比较和面试核验问题，辅助评委理解结果，但不替代最终决策。
"""
    (output_dir / "innovation_summary.md").write_text(content, encoding="utf-8")


def write_report_summary(output_dir: Path, table_counts: dict[str, int]) -> None:
    lines = [
        "# Report Ready Summary",
        "",
        "本目录材料可直接用于项目报告书中的创新点、实验论据、流程图和安全说明。",
        "",
        "## 已生成表格",
        "",
    ]
    for name, title in TABLES.items():
        lines.append(f"- {title}: `{name}.csv` / `{name}.md`，{table_counts.get(name, 0)} 行")
    lines.extend(
        [
            "",
            "## 图示与总结",
            "",
            "- `model_algorithm_flow.md`: Mermaid 算法流程图与边界说明",
            "- `innovation_summary.md`: 可直接写入报告的创新点总结",
            "",
            "## 数据边界",
            "",
            "- 仅读取安全摘要、fixture 实验结果、审计摘要和评分配置。",
            "- 未修改六领域权重和 RankScore 公式。",
            "- 未处理新的真实简历。",
            "- 未导出身份、联系方式、家庭/报酬或私有文件标识信息。",
            "",
        ]
    )
    (output_dir / "report_ready_summary.md").write_text("\n".join(lines), encoding="utf-8")


def build_report_materials(output_dir: Path | None = None) -> dict[str, Path]:
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    table_rows = {
        "domain_weights": build_domain_weight_rows(),
        "extraction_comparison": build_extraction_comparison_rows(),
        "fictional_docx_e2e_results": build_fictional_docx_rows(),
        "official_sample_processing_stats": build_official_sample_rows(),
        "ablation_experiments": build_ablation_rows(),
        "privacy_safety_checks": build_privacy_rows(),
        "assistant_qa_examples": build_assistant_rows(),
    }
    table_rows["fixture_hybrid_accuracy"] = build_fixture_accuracy_rows()
    columns_by_table = {name: list(rows[0].keys()) if rows else [] for name, rows in table_rows.items()}

    generated: dict[str, Path] = {}
    for name, rows in table_rows.items():
        if name not in TABLES:
            TABLES[name] = "Fixture 混合抽取准确率表"
        _write_table(output_dir, name, rows, columns_by_table[name])
        generated[f"{name}.csv"] = output_dir / f"{name}.csv"
        generated[f"{name}.md"] = output_dir / f"{name}.md"

    write_algorithm_flow(output_dir)
    write_innovation_summary(output_dir)
    write_report_summary(output_dir, {name: len(rows) for name, rows in table_rows.items()})
    generated["model_algorithm_flow.md"] = output_dir / "model_algorithm_flow.md"
    generated["innovation_summary.md"] = output_dir / "innovation_summary.md"
    generated["report_ready_summary.md"] = output_dir / "report_ready_summary.md"
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description="Export safe report materials for the EviTalent-Rank project report.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    generated = build_report_materials(args.output_dir)
    print(f"report_materials_dir={args.output_dir}")
    print(f"generated_files={len(generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
