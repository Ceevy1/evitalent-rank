from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from evitalent.assistant.answer_guardrail import AnswerGuardrail
from evitalent.db import AssistantMessageRecord, AssistantSessionRecord, get_session


class SessionRepository:
    def __init__(self, session: Session | None = None) -> None:
        self.session = session or get_session()

    def ensure_session(self, session_id: str | None, task_id: str | None, domain: str | None, candidate_id: str | None, scope: str) -> str:
        sid = session_id or f"asst_{uuid4().hex[:12]}"
        record = self.session.query(AssistantSessionRecord).filter_by(session_id=sid).one_or_none()
        now = datetime.now(timezone.utc)
        if record:
            record.updated_at = now
        else:
            self.session.add(AssistantSessionRecord(session_id=sid, task_id=task_id, domain=domain, candidate_id=candidate_id, scope=scope, created_at=now, updated_at=now))
        self.session.commit()
        return sid

    def add_message(self, session_id: str, role: str, content_safe: str) -> None:
        self.session.add(AssistantMessageRecord(message_id=f"msg_{uuid4().hex[:12]}", session_id=session_id, role=role, content_safe=content_safe))
        self.session.commit()

    def history(self, session_id: str) -> list[dict]:
        rows = self.session.query(AssistantMessageRecord).filter_by(session_id=session_id).order_by(AssistantMessageRecord.created_at.asc()).all()
        return [{"role": row.role, "content_safe": row.content_safe} for row in rows]

    def clear(self, session_id: str) -> None:
        self.session.query(AssistantMessageRecord).filter_by(session_id=session_id).delete()
        self.session.commit()
