from __future__ import annotations

import streamlit as st


QUESTIONS = {
    "工作台首页": ["如何开始一次候选人分析？", "系统如何保护候选人隐私？", "综合竞争力指数如何计算？"],
    "新建分析任务": ["如何选择评价领域？", "固定 V1 评价规则是什么意思？", "系统如何保护候选人隐私？"],
    "人才排名与对比": ["解释当前排名前三的主要差异", "哪些候选人的材料可信度较高？", "当前有哪些待核验事项？"],
    "候选人详情": ["总结该候选人的三项优势", "为该候选人生成面试核验问题", "该候选人有哪些证据不足之处？"],
    "简历导入与隐私检查": ["为什么需要先进行隐私保护？", "哪些信息不会用于人才评价？"],
}


def render_quick_questions(page_name: str) -> str | None:
    picked = None
    st.caption("快捷问题")
    for question in QUESTIONS.get(page_name, QUESTIONS["工作台首页"]):
        if st.button(question, key=f"quick_{page_name}_{question}", use_container_width=True):
            picked = question
    return picked
