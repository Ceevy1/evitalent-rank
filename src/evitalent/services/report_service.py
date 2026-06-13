from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from evitalent.models.ranking import RankingResult
from evitalent.settings import PROJECT_ROOT


class ReportService:
    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(PROJECT_ROOT / "templates")),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate_ranking_report(self, result: RankingResult, output_path: str | Path | None = None) -> Path:
        path = Path(output_path) if output_path else PROJECT_ROOT / "data" / "outputs" / "html_reports" / f"{result.ranking_id}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        template = self.env.get_template("candidate_report.html.j2")
        html = template.render(result=result)
        path.write_text(html, encoding="utf-8")
        return path
