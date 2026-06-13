from __future__ import annotations

from evitalent.assistant.models import ContextScope

SYSTEM_PROMPT = """你是“人才分析助手”，服务对象是人力资源工作人员。

你只能依据系统提供的匿名、安全、已核验候选人分析上下文回答问题。
你不得猜测上下文中没有出现的候选人事实。
你不得输出姓名、电话、邮箱、出生日期、婚姻情况、家庭情况、薪资、详细地址或原始文件名。
你不得根据性别、年龄、婚姻或薪资对人才进行评价。
你不得直接给出“录用某人”或“淘汰某人”的最终决策。

你可以解释排名依据、比较匿名候选人的经历与成果、总结材料可信度与待核验风险、根据已核验证据生成面试核验问题、解释系统评分规则。

当上下文不足以支持结论时，请明确回答：“当前简历材料不足以支持这一判断，建议在面试或背景调查中进一步确认。”
如果用户问题不依赖具体候选人的简历事实，例如普通对话、系统使用说明、评分规则解释、招聘分析方法或面试问题设计，请正常调用你的知识与推理能力回答，不要套用“当前简历材料不足”的固定回复。

回答涉及候选人事实时，使用以下结构：
1. 综合判断
2. 主要依据
3. 待核验事项
4. 使用边界说明
"""

GENERAL_CHAT_SYSTEM_PROMPT = """你是“人才分析助手”，服务对象是人力资源工作人员。

你可以像本地 Ollama 对话助手一样，直接回答用户关于人才评价、简历分析、人才排名、指标权重、招聘流程、面试核验、系统使用和普通交流的问题。
回答应当自然、完整、专业，优先使用中文。

安全边界：
1. 不输出姓名、电话、邮箱、出生日期、婚姻情况、家庭情况、薪资、详细地址或原始文件名。
2. 不根据性别、年龄、婚姻或薪资对人才进行评价。
3. 不直接给出“录用某人”或“淘汰某人”的最终决策。
4. 如果用户要求判断某个具体候选人的事实、排名、经历或成果，但当前消息没有提供可核验材料，请说明当前简历材料不足以支持该具体判断。
5. 如果问题不依赖具体候选人材料，请不要套用“当前简历材料不足”的固定回复，而要直接回答。
"""


class AssistantPromptBuilder:
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def general_chat_system_prompt(self) -> str:
        return GENERAL_CHAT_SYSTEM_PROMPT

    def build_messages(self, question: str, context: str, history: list[dict] | None = None, scope: ContextScope = ContextScope.system_help) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt()}]
        for item in (history or [])[-6:]:
            messages.append({"role": item["role"], "content": item["content_safe"]})
        messages.append(
            {
                "role": "user",
                "content": f"当前作用范围：{scope.value}\n安全上下文：\n{context}\n\n用户问题：{question}\n请使用中文回答。",
            }
        )
        return messages

    def build_general_chat_messages(self, question: str, history: list[dict] | None = None) -> list[dict]:
        messages = [{"role": "system", "content": self.general_chat_system_prompt()}]
        for item in (history or [])[-6:]:
            messages.append({"role": item["role"], "content": item["content_safe"]})
        messages.append({"role": "user", "content": f"{question}\n请使用中文回答。"})
        return messages
