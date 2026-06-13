from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.assistant.chat_service import ChatService
from evitalent.assistant.models import AssistantChatRequest, ContextScope


def main() -> int:
    started = perf_counter()
    response = ChatService().ask(
        AssistantChatRequest(question="哪些匿名候选人的材料可信度更高，并说明依据。", scope=ContextScope.current_task, task_id="fixture_task", domain="hr")
    )
    print(f"retrieved_chunk_count={response.retrieved_chunk_count}")
    print(f"source_labels={';'.join(response.source_labels)}")
    print(f"safety_passed={response.safety_passed}")
    print(f"elapsed_seconds={round(perf_counter() - started, 4)}")
    print(f"answer_preview={response.answer[:180].replace(chr(10), ' ')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
