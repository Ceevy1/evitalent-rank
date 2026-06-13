from __future__ import annotations

from pathlib import Path

from evitalent.models.ranking import RankingResult
from evitalent.services.report_service import ReportService


def generate_html_report(result: RankingResult, output_path: str | Path | None = None) -> Path:
    return ReportService().generate_ranking_report(result, output_path)
