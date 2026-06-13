from evitalent.achievement_detection.sentence_segmenter import split_achievement_clauses


def test_hr_compound_sentence_split():
    text = "半年内完成关键岗位招聘18人，将招聘完成率提升至91%，并推动核心岗位离职率下降15%"
    clauses = split_achievement_clauses(text)
    assert clauses == ["半年内完成关键岗位招聘18人", "将招聘完成率提升至91%", "推动核心岗位离职率下降15%"]


def test_production_compound_sentence_split_keeps_numbers():
    text = "产出率提升1.2%；原料损耗下降0.6%；上线2套自动化系统"
    clauses = split_achievement_clauses(text)
    assert clauses == ["产出率提升1.2%", "原料损耗下降0.6%", "上线2套自动化系统"]
