"""折叠只用于紧随其后的 if 条件的局部变量。"""

from __future__ import annotations

from rules.api import SemanticRule, SemanticRuleContext, SemanticRuleResult, statement_end, token_depths


def is_volatile_local(tokens: list[str], target: str) -> bool:
    for position, token in enumerate(tokens):
        if token != target:
            continue
        start = position
        while start > 0 and tokens[start - 1] not in {";", "{", "}"}:
            start -= 1
        if "volatile" in tokens[start:position]:
            return True
    return False


def apply(context: SemanticRuleContext) -> SemanticRuleResult:
    """仅折叠 ``local = expression; if (local)`` 的唯一读取。"""
    tokens = context.tokens
    depths = token_depths(tokens)
    result = SemanticRuleResult()

    for position in range(1, len(tokens) - 1):
        target = tokens[position]
        if (target not in context.local_names or depths[position] != 0
                or tokens[position + 1] != "=" or tokens[position - 1] not in {";", "{", "}"}
                or is_volatile_local(tokens, target)):
            continue

        assignment_end = statement_end(tokens, position + 2, len(tokens))
        expression = tokens[position + 2:assignment_end - 1]
        if not expression or target in expression:
            continue

        if assignment_end + 3 >= len(tokens):
            continue
        if tokens[assignment_end] != "if" or tokens[assignment_end + 1] != "(":
            continue
        if tokens[assignment_end + 2] != target or tokens[assignment_end + 3] != ")":
            continue

        if target in tokens[assignment_end + 4:]:
            continue

        result.condition_aliases[target] = expression

    return result


RULE = SemanticRule(
    name="immediate_condition_alias",
    description_zh="仅将赋值后唯一且紧随其后的 if(local) 折叠为 if(expression)；volatile、重复读取和自引用一律保留。",
    apply=apply,
)
