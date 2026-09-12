# 语义展示规则

主程序启动后会按文件名 A–Z 扫描本目录的 `*.py`，跳过 `__init__.py` 和
`api.py`，并动态加载每个文件导出的 `RULE`。规则必须是 `rules.api.SemanticRule`
实例，并且必须提供中文 `description_zh`。

当前规则：

- `call_classification.py`：仅按本地函数索引精确区分 LOCAL 与 EXTERNAL 调用。
- `dead_initializer.py`：仅隐藏可证明在首次读取前被覆盖的无副作用初始化。
- `function_discovery.py`：按 `call_depth` 收集可达本地函数。
- `function_order.py`：将独立分析函数按 A–Z 排序。
- `static_pure_constant.py`：仅将全函数只写一次的最外层纯常量初始化列入 `static`。

新增规则时应使用 `SemanticRuleContext` 读取信息、返回 `SemanticRuleResult`，且
优先选择保守条件：无法证明安全时应保留原始语义行。
