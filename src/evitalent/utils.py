from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def parse_year_month(value: str | None) -> date | None:
    if not value or value.lower() in {"present", "now", "至今"}:
        return None
    value = value.strip().replace(".", "-").replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.date().replace(day=1)
        except ValueError:
            continue
    return None


def months_between(start: str | None, end: str | None) -> int | None:
    start_date = parse_year_month(start)
    end_date = parse_year_month(end) or date.today().replace(day=1)
    if not start_date:
        return None
    return max(0, (end_date.year - start_date.year) * 12 + end_date.month - start_date.month)

