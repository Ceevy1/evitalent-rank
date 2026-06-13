from evitalent.privacy.redactor import redact_text


def test_redaction_masks_sensitive_values_and_preserves_achievements():
    text = (
        "姓名：陆晨\n"
        "性别：女\n"
        "出生年月：1992.05\n"
        "婚姻状况：已婚\n"
        "家庭情况：已婚已育\n"
        "当前薪资：28K/月\n"
        "期望薪资：35K/月\n"
        "手机：13900001234\n"
        "邮箱：demo.hr@example.invalid\n"
        "工作业绩：半年完成关键岗位招聘 18 人，将招聘完成率提升至 91%，GMV 1亿。"
    )
    result = redact_text(text)

    assert "[姓名已脱敏]" in result.redacted_text
    assert "[性别已脱敏]" in result.redacted_text
    assert "[电话已脱敏]" in result.redacted_text
    assert "[邮箱已脱敏]" in result.redacted_text
    assert "[年龄信息已脱敏]" in result.redacted_text
    assert "[家庭信息已脱敏]" in result.redacted_text
    assert "[薪资信息已脱敏]" in result.redacted_text
    assert "招聘 18 人" in result.redacted_text
    assert "91%" in result.redacted_text
    assert "GMV 1亿" in result.redacted_text

    for sensitive in ["陆晨", "1992.05", "已婚", "28K/月", "35K/月", "13900001234", "demo.hr@example.invalid"]:
        assert sensitive not in result.redacted_text

    assert "13900001234" not in str(result.redaction_summary)
    assert "28K" not in str(result.redaction_summary)
    assert result.redaction_summary["phone"] == 1
    assert result.redaction_summary["salary_current"] == 1
