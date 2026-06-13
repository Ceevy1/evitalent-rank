from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from evitalent.official_samples.private_manifest import read_json
from evitalent.official_samples.settings import OfficialSampleSettings


LIMITATIONS = [
    "结果为辅助评价，不是录用决定。",
    "未披露的信息不能视为候选人不具备能力。",
    "销售与研发领域 V1 规则仍需专家校准。",
    "真实使用前仍需要人工复核与背景调查。",
]


def build_safe_html_report(settings: OfficialSampleSettings) -> Path:
    inventory = read_json(settings.inventory_safe_summary_path) if settings.inventory_safe_summary_path.exists() else []
    rankings = read_json(settings.rankings_dir / "all_domains_safe_summary.json") if (settings.rankings_dir / "all_domains_safe_summary.json").exists() else {"domains": {}}
    rows = []
    for domain, payload in rankings.get("domains", {}).items():
        for item in payload.get("ranking", []):
            rows.append(
                "<tr>"
                f"<td>{html.escape(domain)}</td>"
                f"<td>{html.escape(str(item['rank']))}</td>"
                f"<td>{html.escape(item['document_id'])}</td>"
                f"<td>{item['bcs']}</td><td>{item['eci']}</td><td>{item['penalty']}</td><td>{item['rank_score']}</td>"
                f"<td>{html.escape(', '.join(item.get('top_strength_labels', [])))}</td>"
                f"<td>{html.escape(', '.join(item.get('risk_flag_types', [])))}</td>"
                "</tr>"
            )
    inventory_rows = "".join(
        f"<tr><td>{html.escape(row['domain'])}</td><td>{row['document_count']}</td><td>{row['readable_count']}</td><td>{row['unreadable_count']}</td></tr>"
        for row in inventory
    )
    html_text = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>EviTalent Official Samples Safe Report</title></head>
<body>
<h1>EviTalent-Rank 主办方样本安全演示报告</h1>
<p>系统默认仅处理脱敏后的简历文本，排名结果用于比赛分析与辅助评价，不构成最终录用结论。</p>
<h2>样本数量与处理状态</h2>
<table border="1"><tr><th>领域</th><th>文档数</th><th>可读取</th><th>异常</th></tr>{inventory_rows}</table>
<h2>技术路线</h2>
<p>DOCX 解析 -> 隐私脱敏 -> 人工脱敏确认 -> 本地 Ollama 事实抽取 -> Python 标准化与证据校验 -> 固定 V1 权重排名。</p>
<h2>匿名排名</h2>
<table border="1"><tr><th>领域</th><th>排名</th><th>document_id</th><th>BCS</th><th>ECI</th><th>Penalty</th><th>RankScore</th><th>优势标签</th><th>风险类型</th></tr>{''.join(rows)}</table>
<h2>证据 Grounding 统计</h2>
<p>安全报告仅展示统计与标签，不展示私有 evidence quote。</p>
<h2>模型抽取与规则标准化说明</h2>
<p>LLM 只辅助解释脱敏文本中的事实和单条成果，标准事件类型、方向、评分和排名均由 Python 规则引擎生成。</p>
<h2>系统局限</h2>
<ul>{''.join(f'<li>{html.escape(item)}</li>' for item in LIMITATIONS)}</ul>
</body></html>"""
    path = settings.reports_dir / "official_samples_safe_demo.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")
    return path
