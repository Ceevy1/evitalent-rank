from __future__ import annotations

from app.components.assistant_quick_questions import QUESTIONS
from app.components.assistant_scope_selector import default_scope_for_page
from evitalent.assistant.models import ContextScope
from pathlib import Path


def test_assistant_ui_scope_and_quick_questions():
    assert default_scope_for_page("工作台首页") == ContextScope.system_help
    assert default_scope_for_page("候选人详情") == ContextScope.current_candidate
    assert default_scope_for_page("人才排名与对比") == ContextScope.current_task
    assert "解释当前排名前三的主要差异" in QUESTIONS["人才排名与对比"]
    assert "为什么需要先进行隐私保护？" in QUESTIONS["简历导入与隐私检查"]


def test_assistant_dialog_open_state_persists_until_manual_close():
    launcher = Path("app/components/floating_assistant_launcher.py").read_text(encoding="utf-8")
    dialog = Path("app/components/assistant_dialog.py").read_text(encoding="utf-8")
    assert "assistant_dialog_open" in launcher
    assert "assistant_dialog_page" in launcher
    assert "assistant_dialog_page != page_name" in launcher
    assert "st.session_state.assistant_dialog_page = page_name" in launcher
    assert "st.session_state.assistant_dialog_page == page_name" in launcher
    assert "关闭助手" not in dialog
    assert "on_dismiss=_mark_dialog_closed" in dialog
    assert "st.session_state.assistant_dialog_open = False" in dialog
    assert "st.session_state.assistant_dialog_page = None" in dialog
    assert "st.session_state.assistant_dialog_open = True" in dialog
    assert "st.session_state.assistant_dialog_page = page_name" in dialog
    assert "st.container(height=520" in dialog
