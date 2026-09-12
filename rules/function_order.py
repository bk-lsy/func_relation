"""函数展示顺序规则。

保持当前行为：独立分析区的函数名按 Python 字符串自然顺序（A–Z）排序。
本规则只改变展示顺序，不改变可达范围或函数内容。
"""

from __future__ import annotations

from typing import Iterable

from rules.api import FunctionOrderRule


def order(function_names: Iterable[str]) -> list[str]:
    return sorted(function_names)


RULE = FunctionOrderRule(
    name="function_order",
    description_zh="按函数名 A–Z 排序独立分析区，保持当前展示顺序。",
    order=order,
)
