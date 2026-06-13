from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.assistant.assistant_client import AssistantClient
from evitalent.assistant.embedding_client import EmbeddingClient


def main() -> int:
    assistant = AssistantClient().status()
    embedding = EmbeddingClient().health_check()
    print(f"assistant_enabled={assistant.enabled}")
    print(f"assistant_provider={assistant.provider_display_name}")
    print(f"assistant_model={assistant.model_display_name}")
    print(f"assistant_connected={assistant.connected}")
    print(f"embedding_model={EmbeddingClient().model}")
    print(f"embedding_connected={embedding.ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
