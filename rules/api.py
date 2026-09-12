"""规则插件的稳定接口。新增规则只依赖本文件，不依赖主程序内部实现。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Set, Union


@dataclass(frozen=True)
class SemanticRuleContext:
    """传给语义展示规则的只读函数信息。"""

    function_params: str
    tokens: List[str]
    local_names: Set[str]
    parameter_names: Set[str]
    write_counts: Dict[str, int]


@dataclass
class SemanticRuleResult:
    """规则可隐藏的初始化，以及可移至 static 区的初始化。"""

    dead_initializers: Set[str] = field(default_factory=set)
    static_initializers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticRule:
    """可发现的规则定义；description_zh 必须说明规则的保守边界。"""

    name: str
    description_zh: str
    apply: Callable[[SemanticRuleContext], SemanticRuleResult]


@dataclass(frozen=True)
class FunctionDiscoveryContext:
    """函数可达范围规则的输入。"""

    root_name: str
    call_depth: int
    local_function_names: Set[str]
    direct_effects: Callable[[str], List[str]]


@dataclass(frozen=True)
class FunctionDiscoveryRule:
    """决定从根函数收集哪些本地函数。"""

    name: str
    description_zh: str
    discover: Callable[[FunctionDiscoveryContext], List[str]]


@dataclass(frozen=True)
class FunctionOrderRule:
    """决定独立函数分析区的展示顺序。"""

    name: str
    description_zh: str
    order: Callable[[Iterable[str]], List[str]]


@dataclass(frozen=True)
class CallClassificationContext:
    """调用分类规则的输入。"""

    call_name: str
    local_function_names: Set[str]


@dataclass(frozen=True)
class CallClassificationRule:
    """将调用归类为 LOCAL 或 EXTERNAL。"""

    name: str
    description_zh: str
    classify: Callable[[CallClassificationContext], str]


Rule = Union[SemanticRule, FunctionDiscoveryRule, FunctionOrderRule, CallClassificationRule]


def token_depths(tokens: List[str]) -> List[int]:
    """返回每个 token 进入花括号前所在的嵌套深度。"""
    result: List[int] = []
    depth = 0
    for token in tokens:
        result.append(depth)
        if token == "{":
            depth += 1
        elif token == "}":
            depth = max(0, depth - 1)
    return result


def statement_end(tokens: List[str], start: int, end: int) -> int:
    """返回当前简单语句结尾分号后的下标。"""
    parens = brackets = 0
    for position in range(start, end):
        token = tokens[position]
        parens += token == "("
        parens -= token == ")"
        brackets += token == "["
        brackets -= token == "]"
        if token == ";" and not parens and not brackets:
            return position + 1
    return end


def is_pure_constant(token: str) -> bool:
    """当前源级模型认可的字面量或枚举式常量。"""
    import re

    return bool(
        re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", token)
        or re.fullmatch(r"[A-Z][A-Z0-9_]*", token)
        or (len(token) >= 2 and token[0] in {'"', "'"} and token[-1] == token[0])
    )
