"""筛除可证明未被读取的局部初始化。

仅认可函数作用域内 ``TYPE local = parameter-or-number;`` 这一极窄形式。
局部变量的第一次后续引用必须是顶层 ``local = ...`` 覆盖；循环、跳转、
switch 或任何提前引用都会拒绝筛除。宁可保留噪声，也不隐藏可能的行为差异。
"""

from __future__ import annotations

import re

from rules.api import SemanticRule, SemanticRuleContext, SemanticRuleResult, statement_end, token_depths


def apply(context: SemanticRuleContext) -> SemanticRuleResult:
    tokens = context.tokens
    depths = token_depths(tokens)
    result = SemanticRuleResult()
    for index, token in enumerate(tokens[:-2]):
        if token != "=" or depths[index] != 0:
            continue
        target = tokens[index - 1]
        if target not in context.local_names:
            continue
        statement_start = index - 1
        while statement_start > 0 and tokens[statement_start - 1] not in {";", "{", "}"}:
            statement_start -= 1
        declaration = tokens[statement_start:index]
        if len(declaration) != 2 or declaration[1] != target or not re.fullmatch(r"[A-Za-z_]\w*", declaration[0]):
            continue
        end = statement_end(tokens, index + 1, len(tokens)) - 1
        initializer = tokens[index + 1:end]
        if (len(initializer) != 1
                or (initializer[0] not in context.parameter_names
                    and not re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", initializer[0]))):
            continue

        unsafe = False
        replacement = -1
        for position in range(end + 1, len(tokens)):
            if tokens[position] in {"goto", "for", "while", "do", "switch", "case"}:
                unsafe = True
                break
            if tokens[position] != target:
                continue
            previous = tokens[position - 1] if position else ""
            if (depths[position] == 0 and position + 1 < len(tokens)
                    and tokens[position + 1] == "=" and previous in {";", "}"}):
                replacement = position
            else:
                unsafe = True
            break
        if not unsafe and replacement >= 0:
            result.dead_initializers.add(target)
    return result


RULE = SemanticRule(
    name="dead_initializer",
    description_zh="筛除在首次读取前被确定覆盖的无副作用局部初始化。",
    apply=apply,
)
