from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import streamlit as st

DEFAULTS = {
    "selected_task_id": None,
    "selected_domain": "hr",
    "selected_candidate_id": None,
    "selected_ranking_id": None,
    "uploaded_document_ids": [],
    "uploaded_document_ids_by_task": {},
    "redacted_document_rows_by_task": {},
    "analysis_processing_rows_by_task": {},
    "extracted_candidate_ids_by_task": {},
    "task_ranking_ids": {},
    "redaction_review_confirmed_ids": [],
    "current_page_context": {},
    "business_mode": True,
    "technical_acceptance_mode": False,
    "tasks": {},
}


def init_session_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value


def create_task(task_name: str, domain: str, job_title: str, focus: str = "") -> str:
    init_session_state()
    task_id = f"task_{uuid4().hex[:8]}"
    st.session_state.tasks[task_id] = {
        "task_id": task_id,
        "task_name": task_name,
        "domain": domain,
        "job_title": job_title,
        "focus": focus,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    st.session_state.selected_task_id = task_id
    st.session_state.selected_domain = domain
    st.session_state.selected_candidate_id = None
    st.session_state.selected_ranking_id = None
    st.session_state.uploaded_document_ids_by_task.setdefault(task_id, [])
    st.session_state.redacted_document_rows_by_task.setdefault(task_id, [])
    st.session_state.analysis_processing_rows_by_task.setdefault(task_id, [])
    st.session_state.extracted_candidate_ids_by_task.setdefault(task_id, {})
    return task_id


def current_task() -> dict | None:
    init_session_state()
    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        return None
    return st.session_state.tasks.get(task_id)


def set_selected_candidate(candidate_id: str) -> None:
    st.session_state.selected_candidate_id = candidate_id


def can_start_analysis(document_rows: list[dict]) -> bool:
    if not document_rows:
        return False
    return all(row.get("safety_passed") is True and row.get("review_confirmed", False) for row in document_rows)


def official_review_confirmed(gate_payload: dict | None) -> bool:
    return bool(gate_payload and gate_payload.get("review_confirmed") is True)
