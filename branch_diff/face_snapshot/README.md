# face_snapshot：AC/BC 摸排记录（2026-10-09）

本记录按上层 [研究口径](../README.md) 建立可复现的阶段 A 基线及阶段 B/C/D 的已核实入口。完整的 95 笔焦点路径非合并提交、实际改动文件和增删行见 [commits.md](commits.md)。**当前没有人工等价确认、关系链完整性确认，也没有得出可直接 cherry-pick 的提交清单。** 已创建生成器输入并做隔离运行验证；未改 CAP 业务代码。

生成器读取本目录的 [`scope.json`](scope.json)、[`dependencies.json`](dependencies.json)、[`equivalent_pairs.json`](equivalent_pairs.json)、[`relation_confirms.json`](relation_confirms.json)。当前 30 条 AC 与 65 条 BC `relation_confirm` 全部为 `0`；无已确认的等价对。空 `related_chain` 只表示**尚未录入关联提交**，绝不表示已查明无依赖。两条已录入跨仓链仍是未确认候选；三笔 BC 整合提交仅在 `scope.json` 标注为整合候选，不排除出图。

在 `func_relation/` 运行 `python3 generate_branch_diff.py` 可同时生成 `cd_alarm` 和本模块的图；本模块输出至 `outputs/branch_diff/face_snapshot/`。本次也已单独生成该目录的 AC/BC SVG、JSON 和 DFS 顺序文本。生成器现按 `--full-history <opposite>..<side>` 搜索焦点提交，避免漏掉 AC 的 `6f4f42d77`。如任一 ref 变化，先重做候选、依赖和确认状态核对，再运行生成器。

## 1. 固定输入

全部 SHA 为本地已有远端跟踪 ref 的快照；本次未 fetch。每个仓库独立计算共同祖先。

| 仓库 | AC tip | BC tip | 共同祖先 |
| --- | --- | --- | --- |
| `NVMP/nvmp/tp_package/cap` | `178f33f6da6a70893faecea14b1b51ef64bc62ac` | `3e40aa2606ea54ff93f9b39deeddb7cd970d351b` | `af14c8cbad7af217cfe0dc7704bb8f63d8797fdd` |
| `NVMP` | `e8e42a9c2a084a31a4e08125c72fb99ae765d20c` | `225dd89528d8633323cd83de4a3477530b933d1e` | `59ccc081030786a29ba0b714af86b7a54ea82551` |
| `NVMP/nvmp/tp_package/avts` | `c3a6abfba09cdaa8ff76202512e516632b8e71a8` | `bea4558c5dc87d2f57e1ec728ad769455764fc38` | `e5846273c0f1c63f1909dc3f7505d63d8d236061` |
| `NVMP/nvmp/tp_package/nsd` | `8d9a7102fd9a36264ba7cdf381d379f0953f285a` | `4ec42ba42967aa5cfecb8f7f09ae690912287c8a` | `28f452f304e65cadf3f71791f28c4bd88602bd1d` |

焦点路径是 CAP 的 `src/modules/face_snapshot/` 全部跟踪文件。共同祖先该路径为空；AC tip 31 个文件，BC tip 32 个文件。按上层口径的 `--full-history --reverse --topo-order --no-merges` 搜索并逐笔检查路径补丁，AC 30 笔、BC 65 笔，95 笔均有非空路径补丁。普通路径日志会漏掉 AC 的 `6f4f42d77fdf07a6c131bc5f864da85f3cc71a82`，它确实修改 `face_control.c`、`face_storage.c`。在这 95 笔路径补丁之间没有相同的稳定 patch-id，也没有相同的 Change-Id；这两项阴性结果不能证明没有行为等价。

`git diff AC BC -- src/modules/face_snapshot` 有 20 个文件条目：18 个内容不同、`ring_object.c/.h` 仅 mode 不同，另有 BC 独有 `files_ac/etc/default/face_snapshot/storage_head_info`。BC `files_ac` 的该文件 blob 与 AC `files` 的该文件相同（`9dfc5d215a83d6983a7b25e435f519eb3eb8bc50`）；BC 原 `files` 中 `sub_version=2,max_face_num=20`，AC 是 `sub_version=1,max_face_num=50`。这涉及默认存储布局，不能按普通文本配置冲突处理。

## 2. 合并提交与整合候选

`git log --merges AC...BC -- <焦点路径>` 给出 10 笔路径相关合并提交。扩大到 `git rev-list --full-history --merges AC...BC -- <焦点路径>` 得到 98 笔需审计的合并节点；对这 98 笔逐笔执行 `git show --remerge-diff --format= <SHA> -- <焦点路径>`，均无重合并差异输出。因此这次没有发现**相对 Git 重合并结果的手工解决补丁**；这不消除父提交引入的功能差异，也不是构建或运行证明。

BC 的三笔非合并“整合 AC 逻辑”提交仍是 BC 物理独有焦点提交：`be46f65124e1a38b0538e0a1096c8846e80feff3`（索引 BC 60.0，特征/存储基础、头文件、`fss.c`）、`f96c42168ed1262f07bb1afb6240645ad4e24ff6`（BC 61.0，统计/图像存储、默认配置）、`bb3085b88fbccd3b515d2ee7859417e807b7180f`（BC 62.0，`face_control.c`）。提交正文均说明通过 `AC_ON_BC` 和 `BC_ON_AC` 保留两侧版本，但所引的 AC 节点 `e08351f06c0a24ad6b1c98ed0b8376a36dc1007b` **不是当前 AC tip 的祖先**。因此正文中的当时逐文件对齐自测不能外推为当前 AC tip 已整合。后续 BC 63.0、64.0、65.0 又修改了 `face_control.c`；尤其 BC 65.0 改动 PSS 识别与合格事件上报，必须以最终 BC tree 核对。

三个整合提交的路径补丁都已入 [索引](commits.md)，但与 AC 各提交的逐函数、逐条件等价关系仍待建立；当前没有将它们硬配为一对一等价提交，也无人工确认依据。

## 3. 模块行为域与编译/安装边界

| 行为域 | 文件/已见证据 | 当前判断 |
| --- | --- | --- |
| 数据模型及管理 | `fss.c`、`face_control.*`；AC 1.0/2.0 与 BC 1.0/3.0 分别引入基础实现 | 两侧初始功能同类，提交对象与后续行为已分叉；不能按标题配对确认。 |
| 特征与识别 | `face_feature.*`、`face_control.c`；BC 有 iqa 阈值、场景特征更新、PSS 识别后打合格标签，AC 有 telemetry 与相机日志路径 | 需按宏、签名、阈值和最终调用链比较。 |
| 存储/升级 | `face_storage.*`、`fd_stg_version/*`、`pss_enhance/*`、默认 `storage_head_info` | `FD_SUB_VERSION`、`fd_fixed_faceinfo` 布局、回调返回值和默认容量有分支差异；迁移和掉电恢复需单独验证。 |
| 统计/上报 | `fd_statistics*`；BC 对电池机有 `TP_TAPO_BATTERY_CAM` 条件，整合提交保留 AC 非电池机上报路径 | 条件编译影响类型、定时器和上报 API 是否存在。 |
| 产品配置 | `Makefile`、`NVMP/nvmp/unified_cflags.mk`、默认文件 | `CONFIG_FDS_VERSION_UPGRADE_ENABLE=y` 才加入 `fd_stg_version/*.c`；`CONFIG_FACE_PSS_SUPPORT=y` 才加入 `pss_enhance/*.c`，公共构建标志再分别定义 `FDS_VERSION_UPGRADE_ENABLE`、`FACE_PSS_SUPPORT`。需针对具体产品 profile 验证。 |

BC tip `Makefile` 在定义 `AC_ON_BC` 时复制 `files/*` 后再用 `files_ac/*` 覆盖；未定义 `BC_ON_AC` 时还复制 `files/*`。头文件中这两个宏也控制互斥类型/宏定义，例如 `face_storage.h` 的 `FD_SUB_VERSION` 和 `face_info_up_cb`。**要选用 BC tree 中的 AC 版本，需同时定义 `AC_ON_BC` 与 `BC_ON_AC`**；若只定义前者，两个版本可能同时展开，安装时 AC 覆盖文件还可能被 BC 默认文件再次覆盖。仓库内搜索到这两个名字用于模块守卫及 Makefile，但未找到对具体产品设置它们的配置；实际产品宏集和安装结果仍未验证。

## 4. 已核实的跨仓接口链

### AC 2.0：基础人脸接口（AC→BC 的“物理独有但对侧已有契约”实例）

CAP `98a66a726bd8182d1b2e84347eae5c4dc4472d20` 引入人脸管理、识别、特征和存储主体。同期 NVMP `a750c5dc9bfbe56a69587038f3cf0de0ab53a7be` 在 `libdms/src/mids.h` 增加 `FSS_MAX_FACE_ON_TRAJ`，并在 `libds/files/etc/dsd_convert.json` 增加 `getFaceDetectionConfig`、`doFaceInfoAdd` 等接口；它在 NVMP AC tip 可达、BC tip 不可达。但 BC tip 的同两处接口仍存在，追溯到 BC 物理提交 `6d056583b20dac251b7174da5cfcea8cd1ecee81`（NVMP BC tip 可达）。因此 AC 的 NVMP 提交**不能直接列为 AC→BC 必须迁入**；当前只证实上述符号/方法在 BC 已有，消息结构字段与所有调用行为尚需逐项比对。这也说明以物理独有提交直接推导“目标侧缺失”会误判。

### AC 26.0：face telemetry（AC→BC）

CAP `1ab529891045131033eef8f7e2b625932f15d02e` 在 `face_control.h/.c` 增加 `fd_telemetry_data` 统计、`get_faces_telemetry_info_callbcak`，并把 `getFaceTelemetryInfo` 注册为 DS 方法；代码受 `TELEMETRY_SUPPORT` 约束。NVMP `369f7ce4520c154095c26ec647cb07c5acdc8c85` 改 `libdms/src/mids.h` 中动态数据 ID；NSD `027937816da2c88a0652fadba720a6129d27707e` 在 `telemetry_collect.c` 发送同名 `getFaceTelemetryInfo` 请求并读取 `qualified_face_cnt`、`unqualified_face_cnt`。三笔在各自 AC tip 可达、各自 BC tip 不可达。这里有具体的请求/响应契约和同一需求系列，可作为 AC→BC 的跨仓链候选；还需复核 NVMP/NSD 后续等价实现、DS 方法定义来源及实际产品是否启用 `TELEMETRY_SUPPORT`，故链完整性 `relation_confirm=0`。缺少消费端会失去该项 telemetry 采集；缺少消息/方法契约可能影响构建或请求处理，具体后果待集成验证。

### BC 34.0：PSS（BC→AC）

CAP `1403e6830e471144cf71112c23175731edee6025` 添加 `pss_enhance` 存储并在 `FACE_PSS_SUPPORT` 路径使用 `PSS_RESULT`、`PSS_RESULT_OBJECT`、`PSS_REID_FEATURE_LEN` 和 `SS_RESULT`。NVMP `0e20e838c139cd976e462ee813a81740d411ea9b` 在 `libdms/src/mids.h` 定义这些结构/常量，在 `libsdm/src/slp_model.h` 和 `unified_cflags.mk` 增加相关接口/编译配置。该 NVMP 提交在 NVMP BC tip 可达、在 NVMP AC tip 不可达；NVMP AC tip 的 `mids.h` 未找到这些符号。因此选择 BC 的 PSS 路径迁至 AC 且启用 `FACE_PSS_SUPPORT` 时，必须补齐这些头文件/算法结果和编译契约，或找到目标侧逐项等价实现。CAP AC tree 已有 PSS 调用点及 `pss_enhance` 文件，但是否在现有产品中启用、与 BC 最终 PSS 行为是否等价，仍未确认；这不是“整个 PSS 功能只在 BC”之结论。BC 65.0 还在此路径增加合格人脸事件标签，须继续追踪其消息消费者和设备视频关联效果。

### 已定位的当前 tip 残差实例

AC 30.0 `178f33f6da6a70893faecea14b1b51ef64bc62ac` 把 `pss_enhance/recog_img_storage.c::cp` 错误退出路径的 `src_fd`、`dst_fd` 判断从 `< 0` 改为 `> 0`。BC tip 中 `AC_ON_BC` 保护的对应 AC 版本仍写 `< 0`。这是整合候选**没有覆盖当前 AC tip 的一个逐行反例**，仅适用于启用该源码/宏的构建。AC 当前 `> 0` 还需对 fd 0 边界另行核对，本记录不将其解释为所有文件描述符场景均正确。

## 5. 双向判断与未闭合项

| 方向 | 已核实范围 | 不能越过的结论边界 |
| --- | --- | --- |
| AC→BC | CAP 30 笔物理独有；BC 三笔整合候选覆盖若干 AC 代码区；telemetry 三仓链；AC 30.0 的 BC AC 路径残差 | 不能把 30 笔都当待迁入，也不能把整合提交的自测视为当前 tip 等价。逐函数/宏比对、存储迁移、其余跨仓链未完成。 |
| BC→AC | CAP 65 笔物理独有；BC PSS、统计、电池机、存储升级及新的人脸识别/推送行为有明确差异；PSS 与 NVMP 结构/编译契约相连 | 不能把 65 笔都当待迁入。AC 已有部分 PSS 代码；最终差异及产品启用条件需逐项确认。 |

下一段优先从 [索引](commits.md) 按拓扑和行为域深度优先核对：先分别还原两侧产品宏集与预处理源码；再逐笔检查三笔 BC 整合提交前后和后续 63.0–65.0；接着对存储版本、默认配置、PSS 消息结构、telemetry、FD 统计、HUB/AVTS/NSD 消费端建立完整跨仓链。每条链需记录触发代码、目标侧可达性或等价实现、缺失后果及适用宏/产品。没有完成此项、模拟应用冲突解决、路径树比较、编译与设备验证前，不给出合入顺序或 `confirm=1` / `relation_confirm=1`。
