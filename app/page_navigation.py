from __future__ import annotations

from typing import Mapping

import streamlit as st


_PAGE_REGISTRY: dict[str, object] = {}


def register_pages(pages: Mapping[str, object]) -> None:
    _PAGE_REGISTRY.clear()
    _PAGE_REGISTRY.update(dict(pages))


def switch_to_page(page_key: str) -> None:
    page = _PAGE_REGISTRY.get(page_key)
    if page is None:
        st.error("目标页面尚未注册，请刷新页面后重试。")
        return
    st.switch_page(page)
