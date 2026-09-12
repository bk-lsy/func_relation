# func_relation

`func_relation.py` analyzes the C functions in a before and after source tree
under one explicit macro profile.  It is deliberately source-only: it does not
build, expand headers, resolve types, or traverse calls outside the selected
module directory.

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 后执行：
python3 func_relation.py
```

The script reads the local `config.yaml` next to itself. It is intentionally
ignored by Git; start by copying `config.example.yaml`. Enter the two Git commit IDs in
`before` and `after`, and set the shared module directory in `source_path`.
For example:

```yaml
before: bf2a733cd1f8e86f8770de92116a25fa40f59ca6
after: WORKTREE
source_path: src/modules/cd_alarm/
```

Set either `before` or `after` to `WORKTREE` to read the current working-tree
files under `source_path`; otherwise provide a Git commit ID. Change that file
when switching the source revision, module, macro profile, or output directory. Use
`--config /path/to/config.yaml` only when you need a separate configuration.

For commit IDs, the script forms Git inputs as `git:COMMIT_ID:source_path` and
reads them with `git ls-tree/show`; no worktree is created. `base_dir`, `profile`, and
`output_dir` are resolved relative to `config.yaml`.

By default, reports are written separately into `./outputs`, for example:

```text
outputs/before.json
outputs/after.json
```

The supported profile syntax is the small YAML subset `MACRO: true|false|N`.
Profiles are part of the evidence: a result applies only to that macro set.

`config.yaml` 中的 `raw_hash`、`structural_hash`、`semantic_hash` 可分别设为
`true` 或 `false`，控制对应哈希字段是否写入报告。每个配置项旁均有中文说明。

## Report fields

Each function gets a `raw_hash`, a conservative `structural_hash`, its direct
call names in `direct_effects`, a normalized token count, a `semantic_hash`, and a readable
`semantic` behavior view. The before/after reports have exactly the same
schema: diffing the two JSON files directly is the comparison.

`semantic.temporal` is a compact behavior-oriented intermediate language:
`IF`/`FOR`/`WHILE` express control, `SET_LOCAL` and `WRITE_STATE` express
state changes, `RETURN` expresses exits, and calls are classified as
`CALL_LOCAL` or `CALL_EXTERNAL`. `semantic.bindings` maps original local names
(sorted A-Z for review) to their normalized identifiers such as `v0`.

`semantic.temporal` is a flat function-analysis view. It collects each
module-local function reachable within `call_depth`, then analyzes every
function independently in A–Z order. A function is listed only once and is
never nested inside its caller; `CALL_LOCAL` still records each direct call in
that function's own analysis.

为减少展示噪声，工具会省略一类可证明无效的局部初始化：仅限函数作用域的
`TYPE local = parameter;`，其右侧是非 `volatile` 参数，并且在变量首次出现
前必须被同一作用域的 `local = ...` 完整覆盖。中间若出现该变量引用、循环、
跳转或复杂声明，工具一律保留初始化。该规则只影响 `semantic.temporal`，不影响
`raw_hash` 或 `structural_hash`。

`semantic.static` contains only independent, pure constant local declarations,
sorted by source identifier, and only when that variable has exactly one direct
write in the function. No calls, memory reads, pointer dereferences, arithmetic
expressions, volatile accesses, or control-flow statements are reordered or
removed.

Module-local calls are expanded recursively by two levels by default. External
calls deliberately remain `CALL_EXTERNAL`; the tool will not guess their
implementation. Set `call_depth` or `max_semantic_lines` in `config.yaml` to
adjust those limits.

The report records direct call names as opaque effects. For example,
`inet_add_timer` and `msg_send` are recorded but their implementations are not
followed. Unsupported conditional expressions are
reported in `diagnostics`; do not treat a report with diagnostics as proof.

This is an MVP.  Its next safe extension is a real C parser (Tree-sitter) for
more complete local declaration/CFG extraction, while keeping the same profile
and JSON-report interfaces.
