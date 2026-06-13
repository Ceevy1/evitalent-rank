from __future__ import annotations

from evitalent.interview.question_template_bank import QuestionTemplateBank


def test_question_template_bank_covers_six_domains_and_key_events():
    bank = QuestionTemplateBank()

    assert set(bank.domains()) == {"hr", "production", "ecommerce", "brand", "sales", "rd"}
    assert "招聘" in bank.get_template("hr", "recruitment_delivery").question_template
    assert "损耗" in bank.get_template("production", "loss_reduction").question_template
    assert "GMV" in bank.get_template("ecommerce", "gmv_growth").question_template
    assert "具体项目" in bank.get_template("unknown", "unknown").question_template
