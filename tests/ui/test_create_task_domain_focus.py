from __future__ import annotations

from pathlib import Path


def test_create_task_domain_focus_updates_outside_form():
    source = Path("app/pages/create_task_page.py").read_text(encoding="utf-8")
    radio_position = source.index('st.radio(')
    form_position = source.index('with st.form("create_task_form")')
    focus_position = source.index('DOMAIN_FOCUS[domain]')

    assert radio_position < form_position
    assert focus_position < form_position
    assert 'key="create_task_domain"' in source
