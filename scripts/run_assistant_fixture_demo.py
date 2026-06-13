from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.assistant.chat_service import ChatService
from evitalent.assistant.models import AssistantChatRequest, ContextScope


QUESTIONS = [
    "为什么当前 HR 第一名排名靠前？",
    "比较两位匿名候选人的成果差异。",
    "为其中一位候选人生成面试核验问题。",
]


def main() -> int:
    service = ChatService()
    session_id = None
    for question in QUESTIONS:
        response = service.ask(AssistantChatRequest(session_id=session_id, question=question, scope=ContextScope.current_task, task_id="fixture_task", domain="hr"))
        session_id = response.session_id
        print(f"question={question}")
        print(f"retrieved_chunk_count={response.retrieved_chunk_count}")
        print(f"safety_passed={response.safety_passed}")
        print(f"answer_preview={response.answer[:180].replace(chr(10), ' ')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
