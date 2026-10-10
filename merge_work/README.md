# face_snapshot 分支收敛当前口径与进度

更新时间：2026-10-11

## 当前基线

- CAP 工作分支：`face_snapshot_converge_1010`
- 收敛起点：本地 `develop/bc_develop_220927`，`3e40aa2606ea54ff93f9b39deeddb7cd970d351b`
- AC 原始 tip：`develop/nvmp_release_1.9.2`，`178f33f6da6a70893faecea14b1b51ef64bc62ac`
- BC 原始 tip：`develop/bc_develop_220927`，`3e40aa2606ea54ff93f9b39deeddb7cd970d351b`
- 当前分支相对 BC 有 4 笔本地收敛提交，工作区干净，未推送。
- CAP 独特焦点提交仍按既有表统计为 AC 30 笔、BC 65 笔；本批只处理 AC 前 5 个编号的已覆盖或明确子范围，没有声称整批功能已经闭合。

## 化学合并口径

依据 `func_relation/化学合并指引.doc` 和 `func_relation/branch_diff/face_snapshot/README.md`：

1. 先以原始 AC/BC 提交和实际补丁为责任单位，沿函数、调用点、状态、数据结构和外部契约闭环判断。
2. 两侧逻辑相同或问题修复对两侧都适用时，直接共用，不为了保留分支而复制代码。
3. 共用业务逻辑或时序确实不同，需要保留两侧旧行为时，才使用 `AC_BC_OPTIMIZE`；不得用它包住无实际差异的代码。
4. `AC_ON_BC`、`BC_ON_AC` 必须按各自语义单独使用；本次已回退 FSS-LOG 收敛提交，不保留类似 `#if defined(AC_ON_BC) || defined(MODULE_LOG_CONTROL)` 的组合条件。
5. 平台、协议、存储布局和外部能力差异不能只为消宏而覆盖；复杂差异需保留最小分支并记录原因。
6. `confirm`、`relation_confirm` 仍不自动设置；源码覆盖、提交等价、依赖链完整、可编译和设备行为是不同证据。

## 已完成的 4 笔本地提交

### 1. `eea101fd3e4117dc6d3eed74fe4009a2dabc4488`

`docs(face_snapshot): account for shared AC base data model`

对应 AC #1 `531e616242...`。确认基础 `fss_data_model()` 和 8 个普通默认文件已经在 BC 存在，因此没有重复迁入业务代码。`storage_head_info` 仍涉及不同存储布局和容量契约；BC `files/` 与 `files_ac/` 的安装选择必须按产品宏核对，不能直接覆盖。

### 2. `03e9468f4e1165a6dbe2eb68e93b0bc34e85d63b`

`refactor(face_snapshot): share base feature loading flow`

对应 AC #2 `98a66a726b...` 的明确子范围：`load_feature()` 和 `fd_feature_load_data()` 的公共读取、临时 JPEG、特征更新、写回、清理流程。分配大小策略按 AC/BC 原行为保留。

复核后将 `img_buf == NULL` 判空移到公共路径：AC、BC 分配失败均返回 `-1`，不继续读图；该保护两侧都适用，不需要 `AC_BC_OPTIMIZE`。AC #2 的控制、存储、阈值等其他范围仍未处理。

### 3. `32a852a6f23e5df2338310f29df84d8ac25bb79a`

`test(face_snapshot): verify BC coverage of AC tag-only changes`

对应 AC #3 `1df1db3902...`。BC `450a0bbeec...` 已包含“同名只改 tag 不报自身冲突”和关闭相似组刷屏日志两处修改，当前 BC tip 仍保留；没有重复迁入。

### 4. `e4f4a3aa9ae60275a19ba05c37143fded79b4819`

`fix(face_snapshot): share snapshot sizing fix`

对应 AC #4 `0c090e6e76...` 的主图读取子范围，采用 BC `1186c1861d...` 的问题修复：AC、BC 都先读取实际图片长度，再按 `max_img_len` 或 `image_len + 32` 分配，避免大图及 AES 原地加密越界。该修复本身同时适用 AC/BC，已去除 `AC_BC_OPTIMIZE` 分流。

AC #4 的通知间隔、陌生人次数、HUB/云端消息策略仍未闭环。

## FSS-LOG 状态

原本的第 5 笔 FSS-LOG 收敛提交 `10f72793918754815589060c004773d58c552541` 已整体回退。当前不修改 FSS-LOG，也不保留其测试和文档变更。后续如处理日志，`AC_ON_BC`、`BC_ON_AC` 必须分别判断，不能使用用户明确禁止的组合形式。

## 验证状态

- 当前 CAP 仓库运行 `python3 tests/face_snapshot/verify_batch1.py`：6 项测试通过。
- `git diff --check develop/bc_develop_220927 HEAD` 通过。
- 测试使用主机 GCC 和 fixture，覆盖 AC/BC 宏、优化宏、tag-only 更新、图片大小边界、分配失败及日志之外的已完成范围；不等于产品交叉编译、链接、设备、APP 或云端联调。
- 当前环境没有产品 `.config`、SDK staging/build 目录和交叉工具链，因此暂不宣称固件构建通过。

## 下一步入口

优先补齐 AC #2 的存储/控制/阈值残余，以及 AC #4 的通知与外部消息链；之后再按 AC/BC 独特提交拓扑推进。每次继续少量提交，先核对对侧已有实现和真实依赖，再决定直接共用、保留最小宏分支或登记外部 TODO。

