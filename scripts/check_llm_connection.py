from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.llm_client import LLMClient
from evitalent.settings import get_settings


def main() -> None:
    settings = get_settings()
    provider = settings.llm_provider or "mock"
    print(f"current_mode={provider}")
    if provider == "mock":
        print("mock mode: no model connection required")
        return
    result = LLMClient(provider=provider).health_check()
    print(f"provider={result.provider}")
    print(f"ok={result.ok}")
    print(f"message={result.message}")


if __name__ == "__main__":
    main()
