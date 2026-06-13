from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class QuestionTemplate:
    question_template: str
    follow_up_template: str
    expected_good_answer_template: str
    red_flags: list[str]
    score_dimension: str


GENERIC_TEMPLATE = QuestionTemplate(
    question_template="请结合一个具体项目说明你在{competency}上的关键贡献和结果。",
    follow_up_template="请补充说明你的个人角色、协作对象、关键难点和结果口径。",
    expected_good_answer_template="能说明背景、目标、本人动作、量化结果、证据口径和复盘反思。",
    red_flags=["只能泛泛描述团队成绩", "无法说明个人贡献", "数据口径前后不一致"],
    score_dimension="岗位匹配与证据可信度",
)


def _template(event_name: str, dimension: str) -> QuestionTemplate:
    return QuestionTemplate(
        question_template=f"你在{event_name}方面取得过结果，请说明当时的业务背景、目标、你的具体动作和最终结果。",
        follow_up_template="如果换到当前岗位，你会如何复用这套方法？哪些条件不同需要调整？",
        expected_good_answer_template="能清楚说明目标、动作、资源约束、本人贡献、结果口径和可迁移经验。",
        red_flags=["无法解释数据来源", "把团队贡献完全等同于个人贡献", "缺少复盘和迁移思考"],
        score_dimension=dimension,
    )


TEMPLATES: dict[str, dict[str, QuestionTemplate]] = {
    "hr": {
        "recruitment_delivery": _template("招聘交付", "招聘交付能力"),
        "recruitment_completion_rate": _template("招聘完成率提升", "招聘达成能力"),
        "retention_improvement": _template("人才保留改善", "组织与人才管理"),
        "training_system_project": _template("培训体系建设", "人才培养"),
        "performance_system_project": _template("绩效体系建设", "绩效管理"),
        "organization_development": _template("组织发展", "组织推动"),
    },
    "production": {
        "efficiency_improvement": _template("效率改善", "生产效率"),
        "loss_reduction": _template("损耗下降", "成本与损耗控制"),
        "automation_upgrade": _template("自动化升级", "技术改造推动"),
        "quality_improvement": _template("质量改善", "质量管理"),
        "cost_reduction": _template("成本下降", "成本控制"),
        "delivery_improvement": _template("交付改善", "交付管理"),
    },
    "ecommerce": {
        "gmv_growth": _template("GMV 增长", "业务增长"),
        "roi_improvement": _template("ROI 改善", "投放效率"),
        "conversion_improvement": _template("转化率提升", "转化优化"),
        "live_content_operation": _template("直播内容运营", "内容运营"),
        "private_domain_operation": _template("私域运营", "用户运营"),
    },
    "brand": {
        "gmv_growth": _template("GMV 增长", "商业增长"),
        "revenue_growth": _template("收入增长", "商业成果"),
        "product_launch": _template("产品上市", "新品推进"),
        "brand_zero_to_one": _template("品牌从 0 到 1", "品牌冷启动"),
        "brand_repositioning": _template("品牌重定位", "品牌策略"),
        "campaign_operation": _template("营销活动运营", "传播与活动"),
    },
    "sales": {
        "revenue_growth": _template("销售收入增长", "销售增长"),
        "collection_performance": _template("回款表现", "回款管理"),
        "channel_expansion": _template("渠道拓展", "渠道建设"),
        "key_account_growth": _template("大客户增长", "客户拓展"),
        "target_completion": _template("目标达成", "销售达成"),
    },
    "rd": {
        "patent_publication": _template("专利成果", "研发成果"),
        "product_launch": _template("产品上市", "产品研发"),
        "technology_transfer": _template("技术转化", "技术转化"),
        "technical_breakthrough": _template("技术突破", "技术深度"),
        "rd_project_delivery": _template("研发项目交付", "项目交付"),
    },
}


class QuestionTemplateBank:
    def get_template(self, domain: str, event_type: Optional[str]) -> QuestionTemplate:
        return TEMPLATES.get(domain, {}).get(str(event_type or ""), GENERIC_TEMPLATE)

    def domains(self) -> list[str]:
        return list(TEMPLATES)
