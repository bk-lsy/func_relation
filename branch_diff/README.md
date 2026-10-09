# face_snapshot：AC/BC 分支差异研究口径

## 1. 研究目标与当前阶段

本研究回答两个方向的问题：将 AC 的 `face_snapshot` 能力合入 BC，需要处理哪些实际差异提交、跨模块刚需提交和外部契约；反方向将 BC 能力合入 AC 时亦然。结论必须区分 Git 物理提交、已在对侧实现的等价行为、仍缺失的行为，以及合入后才能验证的运行结果。

本文件仅规定分析范围、证据标准和分段顺序。它**不是**已确认的提交清单、依赖清单或合入方案；当前不据此改动 CAP 业务代码，也不将 `cd_alarm` 的人工确认结果迁移到本模块。

## 2. 固定输入与可复现基线

| 项目 | 本次口径 |
| --- | --- |
| 焦点仓库 | `NVMP/nvmp/tp_package/cap`（CAP 独立 Git 仓库） |
| AC ref | `origin/develop/nvmp_release_1.9.2` |
| BC ref | `origin/develop/bc_develop_220927` |
| 焦点路径 | `src/modules/face_snapshot/` 下的全部跟踪文件，包含 `files/`、`files_ac/`、`fd_stg_version/`、`pss_enhance/` 等子目录 |
| 本地 AC tip | `178f33f6da6a70893faecea14b1b51ef64bc62ac` |
| 本地 BC tip | `3e40aa2606ea54ff93f9b39deeddb7cd970d351b` |
| CAP 共同祖先 | `af14c8cbad7af217cfe0dc7704bb8f63d8797fdd` |

以上 SHA 是 2026-10-09 对**本地已有远端跟踪 ref** 的只读快照，没有执行 `fetch`。继续分析或生成图时先记录当次 ref SHA；ref 变化后重算提交集合与差异，不能沿用旧编号和旧确认结论。各外部仓库（NVMP、AVTS、NSD 等）应分别记录其 AC/BC ref、tip 和共同祖先，不能套用 CAP 的共同祖先。

共同祖先的焦点路径为空；AC tip 有 31 个该路径下的跟踪文件，BC tip 有 32 个。`git diff AC BC -- src/modules/face_snapshot` 的方向是“AC 变成 BC”，其中 `files_ac/etc/default/face_snapshot/storage_head_info` 显示为新增，即该路径目前只在 BC tip 中；不能从文件名推断其功能归属。

## 3. 差异提交的定义

1. **物理独有**：AC 候选集合是 `BC..AC` 中修改焦点路径的提交；BC 候选集合是 `AC..BC` 中修改焦点路径的提交。这里的“独有”只表示提交对象在对侧 tip 的祖先图中不可达，不表示功能一定缺失。
2. **候选发现**：使用 `git rev-list --full-history --reverse --topo-order --no-merges <opposite>..<side> -- src/modules/face_snapshot` 获取非合并候选。`--full-history` 用于避免路径历史简化漏掉有效提交；逐提交核对该提交对焦点路径的实际补丁。当前快照下，AC 为 30 个，BC 为 65 个。普通路径日志会把 AC 缩为 29 个，漏掉确实修改 `face_control.c`、`face_storage.c` 的 `6f4f42d77`，因此不能用普通日志数量作完整性证明。
3. **合并提交单列审计**：`--no-merges` 只用于先建立非合并提交集合；另行检查路径相关的合并提交是否引入合并解决内容，不能把“被排除在候选列表外”理解为“没有路径影响”。
4. **文件结果差异**：独立比较两个 tip 的路径树、文件列表及逐文件内容。提交集合、提交标题和最终文件差异是三类证据；任何一类不能代替其他两类。
5. **重命名与配置**：检查跨目录移动、同名文件的不同安装位置、Makefile 条件编译和默认配置。尤其记录 `CONFIG_FDS_VERSION_UPGRADE_ENABLE`、`CONFIG_FACE_PSS_SUPPORT` 对源码集合的影响；更多宏以实际代码与产品配置为准。

在 `func_relation/` 目录执行以下只读查询，可复核当前 CAP 候选集合与文件结果差异：

```bash
git -C ../NVMP/nvmp/tp_package/cap rev-list --full-history --reverse --topo-order --no-merges origin/develop/bc_develop_220927..origin/develop/nvmp_release_1.9.2 -- src/modules/face_snapshot
git -C ../NVMP/nvmp/tp_package/cap rev-list --full-history --reverse --topo-order --no-merges origin/develop/nvmp_release_1.9.2..origin/develop/bc_develop_220927 -- src/modules/face_snapshot
git -C ../NVMP/nvmp/tp_package/cap diff --name-status origin/develop/nvmp_release_1.9.2 origin/develop/bc_develop_220927 -- src/modules/face_snapshot
```

继续研究时若需严格复现本次快照，应把上述 ref 替换为上表的完整 tip SHA。提交编号只在固定快照内有效，不把 `N.0` 当成提交身份；持久记录以仓库名和完整 SHA 为准。

## 4. BC 中已有的“AC 逻辑整合”提交

BC 历史中有三笔题为 `merge AC logic in BC` 的非合并提交，应标记为**整合候选**并逐笔核对：

| 提交 | 标题中的范围 | 本次路径内已观察到的主要文件 |
| --- | --- | --- |
| `be46f65124e1a38b0538e0a1096c8846e80feff3` | feature/storage basis | `face_feature.*`、`face_storage.*`、`fss.c` 及相关头文件/版本文件 |
| `f96c42168ed1262f07bb1afb6240645ad4e24ff6` | fd_statistics family + pss storage + default config | `fd_statistics*.c`、`recog_img_storage.c`、`Makefile`、默认配置 |
| `bb3085b88fbccd3b515d2ee7859417e807b7180f` | face_control | `face_control.c` |

这三笔仍属于 BC 的物理独有提交。其标题不能证明任一 AC 提交已被完整覆盖；也不预设将其排除出图或分析。逐笔记录引入前后的 BC 内容、与哪些 AC 改动相交、保留了哪些 BC 行为、遗漏或改写了哪些 AC 行为，以及后续 BC 提交是否再次修改该内容。若确认只是试点或中间态，再单独记录分析范围状态和理由。

## 5. 分段与深度优先顺序

按焦点提交的拓扑顺序推进，每个提交先查其自身补丁，再沿刚需链深度优先查到可验证的叶子，然后才处理下一个焦点提交。提交日期、标题编号（如 `1/2`）只作检索线索，不取代 Git 祖先关系。

| 阶段 | 工作内容 | 该阶段的可验收结果 |
| --- | --- | --- |
| A. 基线 | 固定各仓库 ref SHA、路径树、编译宏/产品场景；审计合并提交 | 可复现输入与覆盖范围 |
| B. 焦点差异 | AC/BC 各自完整历史候选；按文件和行为域拆解，包括数据模型、控制/识别、特征、存储/升级、统计、PSS、默认配置 | 每个焦点提交的实际路径补丁与行为说明 |
| C. 对侧匹配 | 查稳定 patch-id、Change-Id、源提交引用、代码位置及最终行为；核对三笔 BC 整合提交 | 待确认的 AC/BC 等价关系及反例 |
| D. 刚需链 | 从焦点改动触达的数据结构、API、消息、存储格式和调用者逐层查跨仓提交及外部契约 | 对每个焦点提交的完整关联链、证据和缺口 |
| E. 合入判断 | 区分对侧已有、仍缺、冲突需改写、仅特定宏/产品生效；核对最终路径差异与集成验证需求 | 分方向的待合入范围和未验证事项 |

建议展示编号沿用 `N.0` 表示第 N 个修改 `face_snapshot` 的焦点提交；其跨仓提交或外部契约用 `N.1`、`N.2` 等。编号是阅读与 DFS 顺序标记，不是独立的证据。若同一焦点提交也出现在其他焦点提交的关联链中，仍保留自己的 `N.0` 身份，并显式记录两者之间的有向关系，不能重复计作跨仓依赖。

每段完成时交付该段的提交范围、已核实事实、候选关系、证据路径、尚存疑问和下一段入口；没有完成的关系保持待确认。跨阶段遇到前置假设被推翻，应更新依赖它的已记录结论。

## 6. 两种人工确认的边界

**等价确认 `confirm`** 可绑定一对 AC/BC 提交，也可绑定一组 AC 提交与一组 BC 提交，表示在明确的路径、宏配置、产品条件及目标行为下，两侧最终效果经人工核对等价。`confirm=0` 为候选，`confirm=1` 为已确认。相同标题、Change-Id、patch-id 或代码片段都只是证据；patch-id 相同也需检查后续提交是否覆盖/回退了效果。组内提交均保持各自物理独有性和图节点；某提交已由对侧其他提交组合实现时，不应仅因其 SHA 不在对侧祖先中就列为功能缺失。多提交组须在 `equivalent_pairs.json` 的 `groups` 中列出两侧全部成员、行为范围、适用条件、最终状态证据和未决项。

**关系确认 `relation_confirm`** 分 AC、BC 两部分，为该侧每一个 `N.0` 焦点提交记录“原提交 + 完整关联提交链”，无关联提交时链为空。`0` 表示链的完整性和必要性未获人工确认；`1` 表示已核对该链在声明的目标分支与条件下完整、必要。确认绑定整条链；增加、删除、替换或调序关联提交后，应重新核对确认状态。关联链中的外部契约应另列文字及验证方式，不能因提交链确认就视为外部契约已满足。

某提交是“对侧已有等价行为”、某依赖提交“已在对侧祖先中”、以及某接口“需随迁移补齐”，应分别记录。`confirm=1`、`relation_confirm=1` 均不等于可无冲突 cherry-pick、可编译或运行行为一致。

## 7. 刚需与外部依赖的取证标准

只有能指出具体因果关系的项才进入刚需链。例如：焦点补丁调用新 API 或引用新字段/宏；改变消息 ID、生产者或消费者契约；改变持久化格式或迁移顺序；要求另一仓库的对应 `1/N`、`2/N` 提交共同落地。每项需写明源提交、依赖提交的仓库与 SHA、触发代码位置、缺失时的构建或行为后果、目标分支是否已具备，以及证据的适用宏/产品条件。

外部依赖可包括 NVMP 公共模型、AVTS/NSD 消费端、算法或 SDK 能力、PRODUCT 宏配置、默认文件安装路径及设备端联调条件；先证明存在具体耦合，再登记。若本地仓库缺少外部实现，只记录契约及“未验证”，不据提交标题推断其已实现。功能相关、同一需求系列和时间接近均不足以单独证明“刚需”。

## 8. 最终结论的证明门槛

须分别给出 AC→BC 与 BC→AC 的结论，至少列明：物理独有提交、已确认等价提交、整合候选覆盖范围、真正待迁入的功能差异、必须同步的跨仓提交、未在仓库内闭合的外部契约，以及当前不确定项。对改动同一行为的多笔提交，要按最终效果判断，不把中间提交机械相加。

“按顺序复制/cherry-pick 后 `face_snapshot` 一致”只能在选定的提交、冲突解决、宏/产品配置和外部依赖都已固定后验证：记录每一步是否能应用，比较合入后的路径树与目标结果，并检查对侧特有行为是否仍保留。路径树一致只证明文件字节一致；构建、配置迁移和设备行为仍需各自验证。在这些证据齐备前，结论应写为待验证，而不是由提交拓扑直接推得。

## 9. 口径与后续输入的边界

本文件建立分析规则，不充当已确认的关系清单。`face_snapshot/` 现已另建 `scope.json`、依赖与确认状态 JSON 作为 `generate_branch_diff.py` 输入；录入的候选关系均未获人工确认。每次复核仍需保留所用 ref SHA 和人工确认者的依据；脚本生成图只展示当前录入状态，不证明等价、刚需链完整或可合入。
