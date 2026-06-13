from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.extraction.llm_client import LLMClient


def main() -> None:
    client = LLMClient(
        provider="local_ollama",
        base_url="http://127.0.0.1:11434",
        api_key="ollama",
        model="evitalent-extractor:7b",
        temperature=0,
        timeout_seconds=60,
        max_retries=0,
        seed=9,
    )
    result = client.health_check()
    print(f"provider={result.provider}")
    print("model_name=evitalent-extractor:7b")
    print(f"ollama_connected={result.ok}")
    print(f"message={result.message}")
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
