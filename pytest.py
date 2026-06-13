from __future__ import annotations

import os
import sys
from pathlib import Path


def _remove_project_root_from_import_path() -> tuple[Path, list[str]]:
    root = Path(__file__).resolve().parent
    cleaned = []
    for entry in sys.path:
        candidate = Path(entry or ".").resolve()
        if candidate != root:
            cleaned.append(entry)
    original = list(sys.path)
    sys.path[:] = cleaned
    return root, original


if __name__ == "__main__":
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    root, original_path = _remove_project_root_from_import_path()
    from pytest import console_main

    sys.path[:] = original_path
    raise SystemExit(console_main())
