from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "report_materials"
RANKING_SUMMARY_PATH = ROOT / "data" / "outputs" / "official_samples_v1" / "rankings" / "all_domains_safe_summary.json"

DOMAIN_LABELS = {
    "brand": "品牌",
    "ecommerce": "电商",
    "hr": "人力资源",
    "production": "生产",
    "rd": "研发",
    "sales": "销售",
}

COLUMNS = ["领域", "专家评审人数", "候选人数", "Spearman", "Kendall Tau", "Pairwise Accuracy", "NDCG@K", "结论"]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _rankdata_desc(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1], reverse=True)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = rank
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    if len(a) < 2:
        return 1.0
    mean_a = mean(a)
    mean_b = mean(b)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denom_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    denom_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    if denom_a == 0 or denom_b == 0:
        return 1.0 if all(x == y for x, y in zip(a, b)) else 0.0
    return numerator / (denom_a * denom_b)


def _spearman(system_scores: list[float], expert_scores: list[float]) -> float:
    return _pearson(_rankdata_desc(system_scores), _rankdata_desc(expert_scores))


def _kendall_tau_b(system_scores: list[float], expert_scores: list[float]) -> float:
    concordant = discordant = ties_system = ties_expert = 0
    for i in range(len(system_scores)):
        for j in range(i + 1, len(system_scores)):
            sys_diff = system_scores[i] - system_scores[j]
            exp_diff = expert_scores[i] - expert_scores[j]
            if sys_diff == 0 and exp_diff == 0:
                continue
            if sys_diff == 0:
                ties_system += 1
            elif exp_diff == 0:
                ties_expert += 1
            elif sys_diff * exp_diff > 0:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + ties_system) * (concordant + discordant + ties_expert))
    if denominator == 0:
        return 1.0
    return (concordant - discordant) / denominator


def _pairwise_accuracy(system_scores: list[float], expert_scores: list[float]) -> float:
    total = 0
    correct = 0.0
    for i in range(len(system_scores)):
        for j in range(i + 1, len(system_scores)):
            exp_diff = expert_scores[i] - expert_scores[j]
            if exp_diff == 0:
                continue
            sys_diff = system_scores[i] - system_scores[j]
            total += 1
            if sys_diff == 0:
                correct += 0.5
            elif sys_diff * exp_diff > 0:
                correct += 1.0
    return correct / total if total else 1.0


def _minmax(values: list[float]) -> list[float]:
    low = min(values)
    high = max(values)
    if high == low:
        return [50.0 for _ in values]
    return [100.0 * (value - low) / (high - low) for value in values]


def _dcg(relevances: list[float]) -> float:
    return sum((2**rel - 1) / math.log2(index + 2) for index, rel in enumerate(relevances))


def _ndcg_at_k(system_scores: list[float], expert_scores: list[float], k: int) -> float:
    if not system_scores or k <= 0:
        return 1.0
    normalized_relevance = _minmax(expert_scores)
    relevance_0_to_3 = [value * 3.0 / 100.0 for value in normalized_relevance]
    system_order = sorted(range(len(system_scores)), key=lambda index: system_scores[index], reverse=True)[:k]
    ideal_order = sorted(range(len(expert_scores)), key=lambda index: expert_scores[index], reverse=True)[:k]
    actual = _dcg([relevance_0_to_3[index] for index in system_order])
    ideal = _dcg([relevance_0_to_3[index] for index in ideal_order])
    return actual / ideal if ideal else 1.0


def _expert_proxy_scores(ranking: list[dict[str, Any]]) -> list[float]:
    business_scores: list[float] = []
    evidence_scores: list[float] = []
    domain_scores: list[float] = []
    for row in ranking:
        bcs = float(row.get("bcs") or 0.0)
        eci = float(row.get("eci") or 0.0)
        risk_count = len(row.get("risk_flag_types") or [])
        grounded_count = int(row.get("grounded_achievement_count") or 0)
        business_scores.append(0.70 * bcs + 5.0 * grounded_count - 0.50 * risk_count)
        evidence_scores.append(0.75 * eci + 4.0 * grounded_count - 1.25 * risk_count)
        domain_scores.append(0.60 * bcs + 0.25 * eci + 3.0 * grounded_count - 0.75 * risk_count)
    normalized = [_minmax(business_scores), _minmax(evidence_scores), _minmax(domain_scores)]
    return [mean(values) for values in zip(*normalized)]


def _conclusion(domain: str, candidate_count: int, spearman: float, tau: float, pairwise: float, ndcg: float) -> str:
    if candidate_count < 4:
        prefix = "样本量较小，作为初步合理性检查；"
    else:
        prefix = ""
    if min(spearman, tau, pairwise, ndcg) >= 0.90:
        verdict = "排序与3名专家规则代理高度一致。"
    elif spearman >= 0.70 and pairwise >= 0.80 and ndcg >= 0.90:
        verdict = "排序整体合理，局部名次仍建议人工复核。"
    else:
        verdict = "一致性偏低，建议补充真实专家标注后校准权重。"
    if domain in {"sales", "rd"}:
        verdict += " 该领域 V1 模板规则仍需真实专家标注校准。"
    return prefix + verdict


def build_rows() -> list[dict[str, Any]]:
    payload = _read_json(RANKING_SUMMARY_PATH)
    rows: list[dict[str, Any]] = []
    for domain in ["brand", "ecommerce", "hr", "production", "sales", "rd"]:
        domain_payload = payload.get("domains", {}).get(domain, {})
        ranking = domain_payload.get("ranking", [])
        system_scores = [float(row.get("rank_score") or 0.0) for row in ranking]
        expert_scores = _expert_proxy_scores(ranking) if ranking else []
        candidate_count = len(ranking)
        k = min(3, candidate_count)
        spearman = _spearman(system_scores, expert_scores) if ranking else 0.0
        tau = _kendall_tau_b(system_scores, expert_scores) if ranking else 0.0
        pairwise = _pairwise_accuracy(system_scores, expert_scores) if ranking else 0.0
        ndcg = _ndcg_at_k(system_scores, expert_scores, k) if ranking else 0.0
        rows.append(
            {
                "领域": DOMAIN_LABELS.get(domain, domain),
                "专家评审人数": "3（规则代理）",
                "候选人数": candidate_count,
                "Spearman": round(spearman, 4),
                "Kendall Tau": round(tau, 4),
                "Pairwise Accuracy": round(pairwise, 4),
                "NDCG@K": f"{round(ndcg, 4)}@{k}",
                "结论": _conclusion(domain, candidate_count, spearman, tau, pairwise, ndcg),
            }
        )
    return rows


def write_outputs(rows: list[dict[str, Any]], output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ranking_expert_consistency_eval.csv"
    md_path = output_dir / "ranking_expert_consistency_eval.md"
    json_path = output_dir / "ranking_expert_consistency_eval.json"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 排名合理性与专家一致性实验",
        "",
        "说明：当前代码库未包含真实人工专家评分标注，本表为3名专家规则代理的离线一致性测试；真实验收时可用同一脚本替换为人工专家共识排序。",
        "",
        "|" + "|".join(COLUMNS) + "|",
        "|" + "|".join(["---"] * len(COLUMNS)) + "|",
    ]
    for row in rows:
        lines.append("|" + "|".join(str(row[column]).replace("|", "/") for column in COLUMNS) + "|")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "experiment_design": {
            "expert_panel": "3名评审：业务成果评审、证据可信度评审、领域匹配评审；当前为规则代理实现。",
            "system_ranking": "官方样本安全摘要中的 RankScore 排序。",
            "expert_consensus": "三类专家代理分数按域内 min-max 标准化后取均值。",
            "metrics": {
                "Spearman": "系统排序与专家共识排序的秩相关。",
                "Kendall Tau": "系统排序与专家共识排序的成对顺序相关，考虑并列。",
                "Pairwise Accuracy": "专家共识中可判定优劣的候选对，系统排序方向一致的比例。",
                "NDCG@K": "以专家共识分数为相关性，K=min(3,候选人数)。",
            },
        },
        "rows": rows,
        "source": str(RANKING_SUMMARY_PATH.relative_to(ROOT)),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_outputs(rows)
    print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
