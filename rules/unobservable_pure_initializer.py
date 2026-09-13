"""筛除在首次读取前必被函数最外层写入覆盖的纯局部初始化。"""

from __future__ import annotations

from rules.api import SemanticRule, SemanticRuleContext, SemanticRuleResult, is_pure_constant, statement_end, token_depths


def apply(context: SemanticRuleContext) -> SemanticRuleResult:
    """隐藏不影响可观察行为的纯常量或参数快照初始化。

    仅处理函数最外层 ``TYPE local = CONSTANT;``。初始化到下一次函数
    最外层直接赋值之间，``local`` 只能作为普通赋值左值出现；任何读取、取址、
    复合赋值或可能跳过该赋值的控制跳转都会拒绝过滤。
    """
    tokens = context.tokens
    depths = token_depths(tokens)
    result = SemanticRuleResult()

    for index, token in enumerate(tokens[:-2]):
        if token != "=" or depths[index] != 0:
            continue

        target = tokens[index - 1]
        if target not in context.local_names:
            continue

        declaration_start = index - 1
        while declaration_start > 0 and tokens[declaration_start - 1] not in {";", "{", "}"}:
            declaration_start -= 1
        declaration = tokens[declaration_start:index]
        if len(declaration) != 2 or declaration[1] != target:
            continue

        initializer_end = statement_end(tokens, index + 1, len(tokens)) - 1
        initializer = tokens[index + 1:initializer_end]
        if (len(initializer) != 1
                or (not is_pure_constant(initializer[0])
                    and initializer[0] not in context.parameter_names)):
            continue

        overwrite = -1
        for position in range(initializer_end + 1, len(tokens) - 1):
            if (tokens[position] == target and depths[position] == 0
                    and tokens[position + 1] == "="
                    and tokens[position - 1] in {";", "{", "}"}):
                overwrite = position
                break
        if overwrite < 0:
            continue

        safe = True
        for position in range(initializer_end + 1, overwrite):
            token = tokens[position]
            if token == "goto" or (token in {"break", "continue"} and depths[position] == 0):
                safe = False
                break
            if token != target:
                continue
            if position + 1 >= len(tokens) or tokens[position + 1] != "=":
                safe = False
                break

        overwrite_end = statement_end(tokens, overwrite + 1, len(tokens)) - 1
        if target in tokens[overwrite + 1:overwrite_end]:
            safe = False

        if safe:
            result.dead_initializers.add(target)

    return result


RULE = SemanticRule(
    name="unobservable_pure_initializer",
    description_zh="仅隐藏首次读取前必被函数最外层直接赋值覆盖的纯常量或参数快照局部初始化；读取、复合赋值和跳转一律保留。",
    apply=apply,
)
