from __future__ import annotations

DOMAIN_LABELS = {
    "ecommerce": "电商",
    "brand": "品牌",
    "hr": "人力资源",
    "production": "生产",
    "sales": "销售",
    "rd": "研发",
}

DOMAIN_FOCUS = {
    "ecommerce": ["平台运营", "GMV 与销售增长", "投放与转化效率", "内容与直播运营", "团队管理"],
    "brand": ["品牌定位", "品牌升级", "新品牌冷启动", "内容传播", "商业成果"],
    "hr": ["招聘配置", "组织发展", "绩效激励", "人才培养", "业务支持成果"],
    "production": ["生产效率", "质量管理", "成本控制", "自动化改造", "安全合规"],
    "sales": ["销售额", "目标达成", "客户拓展", "回款表现", "团队管理"],
    "rd": ["技术匹配", "产品研发", "专利成果", "技术转化", "项目管理"],
}

FIELD_LABELS = {
    "RankScore": "综合竞争力指数",
    "rank_score": "综合竞争力指数",
    "BCS": "能力表现分",
    "bcs": "能力表现分",
    "ECI": "材料可信度",
    "eci": "材料可信度",
    "Penalty": "风险扣减",
    "penalty": "风险扣减",
    "top_strengths": "核心优势",
    "risk_flags": "待核验事项",
    "grounded_achievement_count": "有依据成果数",
    "eligible_for_scoring": "可纳入比较",
}

STATUS_LABELS = {
    "pending": "等待处理",
    "processing": "正在智能分析",
    "completed_eligible": "可纳入比较",
    "completed_needs_review": "待人工核验",
    "failed_redaction": "隐私处理未通过",
    "failed_schema": "简历信息识别不完整",
    "failed_grounding": "成果依据无法核验",
    "failed_safety": "存在信息安全风险",
    "failed_model_request": "智能分析暂未完成",
    "failed_unknown": "处理异常",
    "manual_approved": "人工核验通过",
    "manual_rejected": "人工核验驳回",
    "manual_needs_follow_up": "需补充核验",
    "issue_confirmed_resolved": "已核验通过",
    "issue_risk_retained": "维持风险提示",
    "issue_needs_material": "需补充材料",
    "domain_mismatch_needs_review": "领域经历需要确认",
    "local_ollama": "本地智能分析服务",
    "grounding_passed": "成果依据已核验",
    "eligible_for_scoring": "可纳入比较",
}

AXIS_LABELS = {
    "education": "教育基础",
    "match": "领域匹配",
    "experience": "相关经验",
    "stability": "稳定性",
    "progression": "成长轨迹",
    "platform": "平台复杂度",
    "management": "管理跨度",
    "competency": "专业能力",
    "achievement": "成果影响",
    "collaboration": "协同领导",
}

EVENT_LABELS = {
    "recruitment_delivery": "招聘交付",
    "recruitment_completion_rate": "招聘完成率",
    "retention_improvement": "人才保留改善",
    "efficiency_improvement": "效率提升",
    "loss_reduction": "损耗降低",
    "quality_improvement": "质量改善",
    "automation_upgrade": "自动化改造",
    "gmv_growth": "GMV 增长",
    "roi_improvement": "投放效率改善",
    "conversion_improvement": "转化改善",
    "revenue_growth": "收入增长",
    "product_launch": "产品上市",
    "patent_publication": "专利成果",
    "technology_transfer": "技术转化",
    "other": "其他成果",
}

STATUS_HELP = {
    "failed_grounding": "部分成果无法在简历材料中找到明确依据，暂不纳入正式排序。",
    "failed_safety": "发现潜在隐私风险，请先核验隐私处理结果。",
    "failed_model_request": "智能分析服务暂未完成本次处理，请稍后重试。",
    "domain_mismatch_needs_review": "候选人经历可能涉及其他领域，请确认是否仍按当前岗位方向比较。",
    "completed_needs_review": "分析完成，但存在待核验事项，默认不纳入正式排序。",
}

BOUNDARY_NOTICE = "本系统结果基于简历中已披露且可核验的信息，用于辅助评价，不构成最终录用决定。"
REPORT_BOUNDARY_NOTICE = "本报告由人才简历综合优选系统生成，评价结果仅反映候选人在已提供简历材料中的可观察经历与成果证据，不构成录用、晋升或淘汰决定。"


def label_for_status(status: str | None) -> str:
    return STATUS_LABELS.get(str(status or ""), "未知状态")


def label_for_domain(domain: str | None) -> str:
    return DOMAIN_LABELS.get(str(domain or ""), str(domain or "未选择"))


def label_for_axis(axis: str) -> str:
    return AXIS_LABELS.get(axis, axis)


def label_for_event(event_type: str | None) -> str:
    return EVENT_LABELS.get(str(event_type or ""), "其他成果")


def is_template_domain(domain: str | None) -> bool:
    return domain in {"sales", "rd"}
