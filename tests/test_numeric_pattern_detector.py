from evitalent.achievement_detection.numeric_pattern_detector import business_numeric_expressions, detect_numeric_expressions


def test_detects_percent_money_person_count_and_period():
    text = "半年内招聘18人，GMV达到1亿元，上线2套系统，产出率提升1.2%，增加0.8个百分点。"
    items = detect_numeric_expressions(text)
    assert any(item.text == "1.2%" and item.unit_type == "percent" for item in items)
    assert any(item.text == "1亿元" and item.unit_type == "money" for item in items)
    assert any(item.text == "18人" and item.unit_type == "person" for item in items)
    assert any(item.text == "2套" and item.unit_type == "count" for item in items)
    assert any(item.text == "半年" and item.unit_type == "period" for item in items)


def test_period_does_not_count_as_business_metric():
    assert business_numeric_expressions("半年内持续推进流程优化") == []
