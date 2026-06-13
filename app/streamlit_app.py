from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _is_running_under_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        return False

    return get_script_run_ctx(suppress_warning=True) is not None


def _run_with_streamlit_cli() -> None:
    from streamlit.web import cli as streamlit_cli

    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    raise SystemExit(streamlit_cli.main())


def main() -> None:
    import streamlit as st

    from app.components.floating_assistant_launcher import render_floating_assistant_launcher
    from app.page_navigation import register_pages
    from app.pages import (
        analysis_history_page,
        candidate_detail_page,
        create_task_page,
        home_page,
        processing_status_page,
        ranking_page,
        report_help_page,
        upload_privacy_page,
    )
    from app.ui_state import init_session_state
    from app.ui_theme import apply_theme

    st.set_page_config(page_title="人才简历综合优选系统", layout="wide")
    apply_theme()
    init_session_state()

    page_registry = {
        "home": st.Page(home_page.render, title="工作台首页", url_path="home", default=True),
        "create_task": st.Page(create_task_page.render, title="新建分析任务", url_path="create-task"),
        "privacy_check": st.Page(upload_privacy_page.render, title="简历导入与隐私检查", url_path="privacy-check"),
        "processing_status": st.Page(processing_status_page.render, title="分析进度", url_path="processing-status"),
        "ranking": st.Page(ranking_page.render, title="人才排名与对比", url_path="ranking"),
        "candidate_detail": st.Page(candidate_detail_page.render, title="候选人详情", url_path="candidate-detail"),
        "analysis_history": st.Page(analysis_history_page.render, title="分析历史记录", url_path="analysis-history"),
        "report_help": st.Page(report_help_page.render, title="报告导出与系统说明", url_path="report-help"),
    }
    register_pages(page_registry)
    pages = list(page_registry.values())

    navigation = st.navigation(pages, position="sidebar")
    navigation.run()
    render_floating_assistant_launcher(getattr(navigation, "title", "工作台首页"))


if __name__ == "__main__":
    if not _is_running_under_streamlit():
        _run_with_streamlit_cli()
    main()
