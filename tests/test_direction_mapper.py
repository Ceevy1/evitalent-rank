from evitalent.normalization.direction_mapper import map_direction


def test_direction_mapping_examples():
    assert map_direction("完成关键岗位招聘18人", "person")[0] == "achieved_amount"
    assert map_direction("将招聘完成率提升至91%", "percent")[0] == "achieved_level"
    assert map_direction("核心岗位离职率下降15%", "percent")[0] == "decrease_by"
    assert map_direction("产出率提升1.2%", "percent")[0] == "increase_by"
    assert map_direction("保持0质量安全事故", "count")[0] == "maintained"
