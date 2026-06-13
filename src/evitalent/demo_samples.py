HR_MULTI_ACHIEVEMENT_TEXT = (
    "某候选人担任人力资源经理，负责招聘配置与组织效率优化。"
    "任职期间完成一线员工招聘120人，将招聘完成率提升至88%。"
    "半年内完成关键岗位招聘18人，将招聘完成率提升至91%，并推动核心岗位离职率下降15%。"
)

PRODUCTION_MULTI_ACHIEVEMENT_TEXT = (
    "某候选人担任生产经理，主导生产管理和工艺优化。"
    "推动产出率提升1.2%；原料损耗下降0.6%；上线2套自动化系统；保持0质量安全事故。"
)

ECOMMERCE_MULTI_ACHIEVEMENT_TEXT = (
    "某候选人负责电商运营和投放优化。"
    "8个月GMV达到1亿元；转化率提升至12%；ROI达到1.5。"
)

EXPECTED_EVENTS = {
    "hr": [
        ("recruitment_delivery", "achieved_amount", 120),
        ("recruitment_completion_rate", "achieved_level", 88),
        ("recruitment_delivery", "achieved_amount", 18),
        ("recruitment_completion_rate", "achieved_level", 91),
        ("retention_improvement", "decrease_by", 15),
    ],
    "production": [
        ("efficiency_improvement", "increase_by", 1.2),
        ("loss_reduction", "decrease_by", 0.6),
        ("automation_upgrade", "achieved_amount", 2),
        ("quality_improvement", "maintained", 0),
    ],
    "ecommerce": [
        ("gmv_growth", "achieved_level", 1),
        ("conversion_improvement", "achieved_level", 12),
        ("roi_improvement", "achieved_level", 1.5),
    ],
}
