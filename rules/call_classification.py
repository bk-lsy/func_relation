"""调用分类规则。

保持当前保守模型：仅当调用名恰好存在于当前模块收集到的函数名集合中，才标记为
``LOCAL``；其他调用一律标记为 ``EXTERNAL``，不猜测头文件、链接符号或宏展开结果。
"""

from __future__ import annotations

from rules.api import CallClassificationContext, CallClassificationRule


def classify(context: CallClassificationContext) -> str:
    return "LOCAL" if context.call_name in context.local_function_names else "EXTERNAL"


RULE = CallClassificationRule(
    name="call_classification",
    description_zh="仅按本地函数索引精确分类调用；无法确认的调用一律为 EXTERNAL。",
    classify=classify,
)
