import pytest

from evitalent.extraction.prompt_builder import PromptBuilder, PromptSecurityError, RedactedResumeInput


def test_prompt_builder_rejects_unredacted_flag():
    builder = PromptBuilder()
    with pytest.raises(PromptSecurityError):
        builder.build(RedactedResumeInput("doc_test", "姓名：张三 电话：13812345678", redaction_completed=False))


def test_prompt_builder_builds_safe_prompt():
    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build(
        RedactedResumeInput(
            document_id="doc_safe",
            redacted_text="个人信息：[姓名已脱敏]\n工作经历：负责招聘配置，半年完成关键岗位招聘 18 人。",
            redaction_completed=True,
            target_domain="hr",
        )
    )
    assert "不得输出排名" in system_prompt or "不决定最终排名" in system_prompt
    assert "不得猜测" in system_prompt
    assert "doc_safe" in user_prompt
    assert "13812345678" not in user_prompt


def test_prompt_builder_rejects_remaining_sensitive_values():
    builder = PromptBuilder()
    with pytest.raises(PromptSecurityError):
        builder.build(RedactedResumeInput("doc_leak", "电话：13812345678\n工作成果：完成招聘 18 人", True))
