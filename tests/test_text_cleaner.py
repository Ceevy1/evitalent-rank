from evitalent.parser.text_cleaner import clean_text, split_sections


def test_clean_text_preserves_business_numbers_and_dates():
    raw = "工作业绩\n\n\n GMV   1亿，转化率提升 30%。\n2020.01-2022.06 任运营经理。\n产出率提升 1.2%。"
    cleaned = clean_text(raw)

    assert "1亿" in cleaned
    assert "30%" in cleaned
    assert "2020.01-2022.06" in cleaned
    assert "1.2%" in cleaned
    assert "\n\n\n" not in cleaned


def test_split_sections_preserves_paragraph_structure():
    text = "个人信息\n候选人编号：C001\n\n教育经历\n本科\n\n工作业绩\n招聘 18 人"
    sections = split_sections(text)

    assert sections["个人信息"] == "候选人编号：C001"
    assert sections["教育经历"] == "本科"
    assert sections["工作业绩"] == "招聘 18 人"
