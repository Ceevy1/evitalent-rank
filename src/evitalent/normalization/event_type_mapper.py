from __future__ import annotations


def map_event_type(text: str, unit: str | None = None) -> tuple[str, str, str]:
    lower = text.lower()
    rules: list[tuple[str, str, str, list[str], set[str] | None]] = [
        ("recruitment_delivery", "招聘交付", "hr_recruitment_delivery", ["招聘人数", "招聘数量", "完成招聘", "引进人才", "引入人才", "到岗", "招聘"], {"person"}),
        ("recruitment_completion_rate", "招聘完成率", "hr_recruitment_completion_rate", ["招聘完成率", "招聘达成率", "到岗率"], {"percent"}),
        ("retention_improvement", "留任改善", "hr_retention_improvement", ["离职率下降", "流失率下降", "人员流失下降"], {"percent"}),
        ("efficiency_improvement", "产出率", "production_efficiency_improvement", ["产出率提升", "生产效率提升"], {"percent"}),
        ("loss_reduction", "损耗率", "production_loss_reduction", ["原料损耗下降", "损耗率下降"], {"percent"}),
        ("automation_upgrade", "自动化升级", "production_automation_upgrade", ["自动称料系统", "自动投加系统", "自动化系统", "引入设备", "上线"], {"count"}),
        ("quality_improvement", "质量安全", "production_quality_improvement", ["质量事故为0", "0质量安全事故", "零安全事故"], None),
        ("gmv_growth", "GMV", "ecommerce_gmv_achieved", ["GMV达到", "GMV完成", "销售额达到", "品牌GMV达到", "新品牌GMV达到"], {"CNY"}),
        ("gmv_growth", "GMV增长", "ecommerce_gmv_growth", ["GMV增长", "销售规模增长"], {"percent"}),
        ("roi_improvement", "ROI", "ecommerce_roi_achieved", ["ROI达到", "投产比达到"], None),
        ("conversion_improvement", "转化率", "ecommerce_conversion_level", ["转化率提升至"], {"percent"}),
        ("conversion_improvement", "转化率", "ecommerce_conversion_increase", ["转化率提升"], {"percent"}),
        ("revenue_growth", "销售额", "brand_sales_growth", ["品牌销售额增长", "年业绩增长", "年销售额达到", "销售收入达到", "销售增长", "收入增长"], None),
        ("product_launch", "产品上市", "product_launch_count", ["新品牌上线", "新品上市", "上市产品", "上线产品", "新品开发完成"], {"count"}),
        ("collection_performance", "回款率", "sales_collection_level", ["回款率达到"], {"percent"}),
        ("channel_expansion", "渠道拓展", "sales_channel_expansion", ["新增客户", "新增门店", "新开渠道"], {"count", "person"}),
        ("patent_publication", "专利", "rd_patent_count", ["获得专利", "授权专利"], {"count"}),
        ("technology_transfer", "技术转化收入", "rd_technology_transfer", ["技术转化收入", "商业化收入"], {"CNY"}),
    ]
    compact = text.replace(" ", "")
    for event_type, metric_name, rule_id, keywords, units in rules:
        if any(keyword.lower() in lower or keyword in compact for keyword in keywords):
            if units is None or unit in units:
                return event_type, metric_name, rule_id
    return "other", "待人工复核", "normalization_needs_review"
