# cd_alarm 分支差异拓扑

本目录只保存 `cd_alarm` 的分析信息，不包含生成脚本，也不固化 AC/BC 独有提交清单。

- `scope.json`：仓库、AC/BC ref、焦点路径和范围标注。
- `dependencies.json`：信息1。定义某个提交合入对向分支时必须同时检查的提交和外部契约。
- `equivalent_pairs.json`：信息2。定义 AC/BC 候选等价提交；每项 `confirm` 初始为 `0`，人工确认后改成 `1`。
- `relation_confirms.json`：分成 `ac`、`bc` 两部分，为两侧每个 `N.0` 焦点提交记录完整 `related_chain`；没有关联提交时链为空。`relation_confirm` 绑定“原提交 + 完整关联链”，初始为 `0`，人工确认后改成 `1`。

仓库根目录的 `generate_branch_diff.py` 会自动扫描 `branch_diff/**/scope.json`。它从对侧 tip 到本侧 tip 的完整路径历史动态搜索焦点路径的物理独有非合并提交，另计算共同祖先，并从完整 Git DAG 计算最近焦点祖先边；形成提交图后，再按信息1深度优先展开依赖。

运行：

```bash
cd ../..
python3 generate_branch_diff.py
```

输出严格分成两张图：

- `outputs/branch_diff/cd_alarm/ac-unique.svg`
- `outputs/branch_diff/cd_alarm/bc-unique.svg`

同时生成对应 JSON 和 DFS 顺序文本。修改 `cd_alarm` 的焦点提交使用 `DFS #N.0`，其跨仓提交和外部契约依赖使用 `DFS #N.1`、`DFS #N.2` 等编号；焦点提交即使同时被另一提交依赖，也仍保持自己的 `N.0` 编号。图中的蓝线是动态计算的 Git 祖先拓扑，红线是信息1依赖。候选等价提交无论 `confirm` 值为何都保留在独有提交图中；`confirm=0` 表示待人工确认，`confirm=1` 表示人工确认等价。`c7f0be052c` 仍作为动态搜到的 BC 独有提交出现，但带 `excluded-pilot` 标记且不参与信息1依赖展开。
