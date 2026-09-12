"""识别可独立展示的纯常量局部初始化。

仅处理函数最外层、单 token 常量的声明初始化，且变量在全函数中只能有一次
直接写入。只要存在后续写入、复杂表达式、嵌套作用域或复杂声明，就保留在时序
分析中，避免错误丢失顺序关系。
"""

from __future__ import annotations

import re

from rules.api import SemanticRule, SemanticRuleContext, SemanticRuleResult, is_pure_constant, statement_end, token_depths


def apply(context: SemanticRuleContext) -> SemanticRuleResult:
    tokens = context.tokens
    depths = token_depths(tokens)
    result = SemanticRuleResult()
    for index, token in enumerate(tokens[:-2]):
        if token != "=" or depths[index] != 0:
            continue
        target = tokens[index - 1]
        if target not in context.local_names or context.write_counts.get(target, 0) != 1:
            continue
        if index < 2 or tokens[index - 2] in {";", "{", "}"}:
            continue
        right_end = statement_end(tokens, index + 1, len(tokens)) - 1
        right = tokens[index + 1:right_end]
        if len(right) == 1 and is_pure_constant(right[0]):
            result.static_initializers[target] = right[0]
    return result


RULE = SemanticRule(
    name="static_pure_constant",
    description_zh="将仅写入一次的最外层纯常量局部初始化移至 static 展示区。",
    apply=apply,
)
