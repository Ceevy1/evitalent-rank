from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.db import init_db
from evitalent.settings import get_settings


def main() -> None:
    init_db()
    print(f"database_initialized={get_settings().resolved_database_url}")


if __name__ == "__main__":
    main()
