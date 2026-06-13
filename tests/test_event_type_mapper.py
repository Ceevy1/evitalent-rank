from evitalent.normalization.event_type_mapper import map_event_type


def test_event_type_mapping_examples():
    assert map_event_type("完成一线员工招聘120人", "person")[0] == "recruitment_delivery"
    assert map_event_type("招聘完成率提升至88%", "percent")[0] == "recruitment_completion_rate"
    assert map_event_type("核心岗位离职率下降15%", "percent")[0] == "retention_improvement"
    assert map_event_type("原料损耗下降0.6%", "percent")[0] == "loss_reduction"
    assert map_event_type("8个月GMV达到1亿元", "CNY")[0] == "gmv_growth"
    assert map_event_type("改善候选人体验", None)[0] == "other"
