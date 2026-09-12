"""本地函数可达范围规则。

保持原有行为：从根函数开始，按调用层数广度收集本地函数；仅当调用深度小于
``call_depth`` 时继续向下发现。函数是否最终展示、以什么顺序展示由其他规则决定。
"""

from __future__ import annotations

from rules.api import FunctionDiscoveryContext, FunctionDiscoveryRule


def discover(context: FunctionDiscoveryContext) -> list[str]:
    distances = {context.root_name: 0}
    pending = [context.root_name]
    while pending:
        caller = pending.pop(0)
        distance = distances[caller]
        if distance >= context.call_depth:
            continue
        for callee in context.direct_effects(caller):
            if callee in context.local_function_names and callee not in distances:
                distances[callee] = distance + 1
                pending.append(callee)
    return list(distances)


RULE = FunctionDiscoveryRule(
    name="function_discovery",
    description_zh="按 call_depth 广度收集根函数可达的本地函数，保持原有截断行为。",
    discover=discover,
)
