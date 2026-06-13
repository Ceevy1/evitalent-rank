from evitalent.parser.text_cleaner import clean_text, split_sections


def test_clean_text_and_split_sections():
    text = "个人信息\n姓名：测试\n\n\n教育经历\n本科\n工作经验\n负责项目"
    cleaned = clean_text(text)
    sections = split_sections(cleaned)
    assert "\n\n\n" not in cleaned
    assert "教育经历" in sections
    assert "工作经验" in sections

