# face_snapshot 分支收敛当前口径与进度

更新时间：2026-10-14

当前有效口径、已跳过/暂缓/撤销的来源提交及仍保留的风险标记，集中见 [当前状态快照](current_status.md)。AC/BC 95 笔原始焦点提交的**动态逐笔进度**见 [`merge_status.json`](../branch_diff/face_snapshot/merge_status.json)；[来源状态清单](source_status.md) 是 2026-10-14 的盘点快照，后续 AC #1/#2/#18/#21 核对见 [本次审查记录](review_20261014.md)。本文件保留逐批推进记录与来源索引。

后续选题按 [完成度与后续方向](mainline.md) 执行：先评估已有合并对原始补丁的覆盖和剩余范围，再以未闭合机制、原始 AC/BC 来源及完整依赖链确定下一项。批次要求的提交数只控制暂停位置，不用于倒推选题。

## 当前基线

- CAP 工作分支：`face_snapshot_converge_1010`
- 收敛起点：本地 `develop/bc_develop_220927`，`3e40aa2606ea54ff93f9b39deeddb7cd970d351b`
- AC 原始 tip：`develop/nvmp_release_1.9.2`，`178f33f6da6a70893faecea14b1b51ef64bc62ac`
- BC 原始 tip：`develop/bc_develop_220927`，`3e40aa2606ea54ff93f9b39deeddb7cd970d351b`
- 当前分支相对 BC 有 44 笔本地提交，工作区干净，未推送；最新为 `c044bebe`。第十四批保留两笔源码提交；原 `0a833bbe` 报表声明收敛已按用户意见撤销，暂不计入已完成范围。
- CAP 独特焦点提交仍按既有表统计为 AC 30 笔、BC 65 笔；本批只处理下文列出的已覆盖或明确子范围，AC #9 跳过，没有声称整批功能已经闭合。

## 化学合并口径

依据 `func_relation/化学合并指引.doc` 和 `func_relation/branch_diff/face_snapshot/README.md`：

1. 先以原始 AC/BC 提交和实际补丁为责任单位，沿函数、调用点、状态、数据结构和外部契约闭环判断。
2. 两侧逻辑相同或问题修复对两侧都适用时，直接共用，不为了保留分支而复制代码。
3. 共用业务逻辑或时序确实不同，需要保留两侧旧行为时，才使用 `AC_BC_OPTIMIZE`；不得用它包住无实际差异的代码。
4. `AC_ON_BC`、`BC_ON_AC` 必须按各自语义单独使用；本次已回退 FSS-LOG 收敛提交，不保留类似 `#if defined(AC_ON_BC) || defined(MODULE_LOG_CONTROL)` 的组合条件。
5. 平台、协议、存储布局和外部能力差异不能只为消宏而覆盖；复杂差异需保留最小分支并记录原因。
6. `confirm`、`relation_confirm` 仍不自动设置；源码覆盖、提交等价、依赖链完整、可编译和设备行为是不同证据。
7. 逻辑合并必须从 AC/BC 原始提交、实际补丁和 BC 已有物理合并出发，不能凭当前代码中发现的一般缺陷另起修复。等价类型别名、函数定义及头文件声明应一起核对；差异只在拼写或重复赋值且语义相同时直接共用。
8. 同一 `[ALL]` 原因或同一机制的相邻收敛范围合为一笔提交，用户明确要求按独立审查范围拆分时除外；先追溯两侧来源。若机制同时适用于 AC/BC，应移除误设的产品分支，让两侧共用完整的初始化、入口和退出路径；核对所有早退分支与锁、资源所有权。
9. 用户要求 rebase 时重写本地未推送提交，合并相同原因的提交，并同步更新源码、声明、测试和审查记录。不得把原先仅保持两侧原样的 token 对比误称为新增共用行为已经验证。
10. 涉及跨模块能力或依赖的原始提交，若当前只审查 CAP 子模块且无法闭环，应标记原始 SHA 和跳过原因，撤销其未完成的局部收敛；不能因其他 CAP 调用点存在就推断平台依赖已满足。
11. 提交来源按实际引入相关代码的原始补丁认定；后续针对同段代码的修复可列为关联提交，不应替代最初来源。rebase 其余提交时保留原补丁，只解决跳过提交造成的冲突及修正来源、进度记录。
12. 一笔原始提交若横跨多个文件或相邻机制，应先核对它的完整补丁与 BC 物理合并，通常在一笔本地提交中落地可共用范围。按用户要求拆分时，应明确列出各笔的边界与同一原始 SHA，合起来审查原提交覆盖范围；对确有产品契约或跨模块依赖的残余分支，应在审查记录中写明原因。
13. 仅有错误打印或格式空格差异的两侧调用直接共用；一侧已有、另一侧没有的简单诊断打印也可两侧共用，并明确记录新增的日志影响。核对原提交时逐项覆盖定义、声明、调用点和相关迁移辅助函数。用户保存的认可提交应作为后续修改的代码起点，不用未经复核的旧结果覆盖。
14. AC/BC 共用的头文件接口，应保留原 AC 公开声明及注释的完整文本，整块提到产品宏范围外，只保留一份；核对两侧宏展开后的可见性，不能删除 AC 原声明后改写成自拟公共块。
15. 收敛时核对共用接口调用方的头文件引用；没有原始补丁或逻辑合并需要支撑的控制流标签、局部变量初值改动应保留原样。文件描述符关闭条件按两侧来源和已确认口径处理。
16. 提交标题含 `(1/2)`、`(2/3)`、`(1/4)` 等分段编号时，先在 CAP 及 NVMP 等相关仓库按标题、问题描述、Change-Id、调用接口和提交时间检索整组关联提交；逐笔核对补丁、分支归属、接口声明/定义及启用条件，再判断是否能逻辑合并。未核完或跨仓库依赖未闭环时，标记整组原始 SHA 和状态，不把单笔局部修改计作整组完成。
17. **每次针对 face_snapshot 执行审查、源码合入、确认已有覆盖、暂缓、撤销或 rebase 后，立即更新 [`merge_status.json`](../branch_diff/face_snapshot/merge_status.json)**：受影响原提交的状态及具体依据/未闭合范围、目标 HEAD 和 `last_action` 均应与动作结果一致。状态未变化的审查也记录结论；同步更新相关批次说明和 commit log，不能只更新后两者。该进度不自动设置候选等价或依赖链的 `confirm` / `relation_confirm`。

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

## 后续两笔本地逻辑合并

### 5. `34edf47b`

`refactor(face_snapshot): share similarity group score selection`。AC #2 的 `fd_feature_get_group_similarity()` 与 BC 基础实现经 `be46f651` 物理合并后保留了重复的最高分赋值及 `uint16_t`/`U16` 双份类型写法。现共用最高分选择，并将实现和头文件声明统一为 `U16 *`。保留阈值及图像质量的真实差异。

### 6. `57628f49`

`refactor(face_snapshot): share faceinfo file synchronization`。AC `63f615946` 与 BC `6fa54768b` 是相同 `[ALL]` 同步锁补丁；BC 物理合并 `be46f651` 只在 BC 宏展开中保留加锁。现把同一 `l_face_info_lock` 的头文件、四个函数入口和退出路径共用于 AC/BC，并合并 `set_faceinfo()` 与 `sync_storage_structure()` 的重复错误出口。初始化函数只在实际取得锁后解锁。存储布局与升级回调仍保留差异。

## 本轮保留 10 笔 CAP 提交（到此暂停）

详细来源、宏范围和证据见 CAP `docs/face_snapshot_converge_1010/batch3.md`。

1. `0d922409`：AC #2 特征图分配共用 BC 大图修复。
2. `0ffe0983`：AC #2 存储文件辅助函数去除仅初始化/诊断差异。
3. `3edc0cbb`：AC #2 相似度阈值 getter 及头文件、调用点共用。
4. `8a3c2ee4`：核实 AC #16 统计链表初始化已由 BC 同补丁覆盖。
5. `94993ca8`：核实 AC #25 最新出现时间修复已由 BC 同补丁覆盖。
6. `ff8e12b7`：核实 AC #12 faceinfo fd 修复已由 BC 同补丁覆盖。
7. `49851998`：核实 AC #19/#20 存储头校验子范围已由 BC 同补丁覆盖。
8. `c1e20d15`：从用户保存的 `a8fcd52b` 继续，依据 AC #8 `747e518a37f12c26f4ea872e98a8d3a7363aad4c` 处理统计事件及错误打印、统计存储接口、报告缓冲区、阈值接口和共用 setter、存储写入格式；`recog_img_storage.c` 在本笔共用四组偏移函数的声明、相同函数体及调用点，并收敛简单初始化。AC 的阈值头文件声明块按原始分支文本保留，并整体提到 AC/BC 宏范围外共用；`face_control.c` 共用 `face_feature.h`。
9. `c035689c`：同属 AC #8，按“不影响实际逻辑”处理 `recog_img_storage.c` 的 `cp()`：共用 20480 字节正常复制流程和 `void` 接口，保留 `0` 初值、`err_exit` 标签、正值 fd 关闭及缓冲区判空释放；补齐打开、分配失败时的简单保护。
10. `6db07dd7`：同属 AC #8，按“影响实际逻辑”处理旧文件扩容及搬移：共用 2048 字节零写，按辅助函数布尔返回值判错，分离图片索引并用 `O_RDWR` 使目标偏移写入生效。修复函数的 `img_data_fd` 初始化和复位保留原有 `0`，退出时仅关闭正值 fd。AC #30 只作 PSS 复制退出路径的后续关联修复。

原 AC #9 `12f602f96c52f1906d4baa5d0413f8dd59567ba7` 涉及跨模块随机源依赖，**标记为跳过、尚未逻辑合并**；本地提交 `71b47a19426083afa5669d86983651987d518fb6` 已在 rebase 中移除。原 `a8725392e7fe5b32ea038e86f0b97f6443e95d52` 与 `9711462f090e8213f508488797a6911491895bd0` 的内容按用户指定边界拆入上述第 8～10 笔，其中回退后未完成的 PSS 范围由第 9、10 笔分别按行为影响收敛；三笔合起来审查 AC #8 的可共用范围。其余提交只随 rebase 改变 SHA、解决由跳过提交造成的文档和测试冲突；生产代码补丁保持原样。

第 4～7 笔为已覆盖范围的实际生产函数验证，没有重复迁入代码；不表示这些原始大提交整体等价。AC #8 的跨模块随机源仍未处理；阈值 setter 的 BC 专有字段保留最小分支，PSS 旧数据迁移已通过主机用例但尚无设备验证，详见 CAP 批次说明。`confirm`、`relation_confirm` 均未自动更改。

## 继续推进的 3 笔 CAP 提交（到此暂停）

详细范围及原始提交依据见 CAP `docs/face_snapshot_converge_1010/batch4.md`。

11. `2cd5c409`：AC #2 `98a66a726` 的 `get_available_index()` 与 BC `450a0bbeec` 经物理合并后仅剩参数名及等价赋值写法分流，现共用函数签名和满额状态输出，不改变槽位选择。
12. `3e44e0dc`：核实 AC #4 `0c090e6e76` 的通知列表配置数据模型、读取和设置接口在两侧已有覆盖；设置函数的后续产品差异保留，尚不声称整条通知链合并完成。
13. `bd41e9fb`：核实 AC #10 `0f8c7c9dfc` 的 HUB 人脸检测判断回退与 BC `d161ecab8a` 相同；两侧 `HUB_MANAGE_SUPPORT` 宏下保留原函数，无重复迁入。

本批只收敛有明确 AC/BC 原始依据的等价代码，或为对侧已覆盖的范围补源级校验；没有改动 PSS 原提交既有迁移公式。`confirm`、`relation_confirm` 继续保持未确认。

## 本轮 3 笔生产代码提交（到此暂停）

详细原始补丁、BC 物理合并来源及保留差异见 CAP `docs/face_snapshot_converge_1010/batch5.md`。本轮已覆盖、无需改生产代码的候选不计入三笔。

14. `0669e92e`：AC #2 `get_similar_score_and_idx()` 的 `uint16_t` 图片索引与 BC `U16` 等价，统一参数和局部变量类型；两侧不同的返回类型及分数选择逻辑保持原样。
15. `565ad246`：AC `de1da536` 与 BC `71c4e67b` 的 FDS/FSS 索引新增事件函数签名及 `0x0`/`0` 清零语句直接共用；事件起始时间的真实产品差异仍分流。
16. `c127b4dd`：将 BC `9aec74acb2` 对 `fds_clean_stg_dir()` 的空路径与两处 `chdir()` 检查完整共用于 AC/BC；主机测试覆盖空路径和进入目录失败，不改成功时的删除流程。

本批未修改原 AC/BC 特有的阈值、数据布局、通知消息时序或跨模块能力。`confirm`、`relation_confirm` 未自动设置。

## 继续推进的 3 笔生产代码提交（到此暂停）

详细来源、宏范围与保留的跨模块边界见 CAP `docs/face_snapshot_converge_1010/batch6.md`。

17. `27e794f4`：BC `7b54cd2e9f` 的统计变量初始化补丁在 AC/BC 公共路径完整共用；时区字符设为 0，出现统计的 `tm/index/found_faceid_flag` 声明和初始化合一，取索引仍在持锁后。
18. `6910c675`：按 BC 基础实现共用 `update_last_time != 0` 的限频条件，修复 AC 启动初期首次出现事件被误抑制；已有记录的间隔规则不变。
19. `7c762a07`：按 BC `0cc155658d` 的定时长度子范围共用每日回收公式及三个常量，将 AC 首次设定处的 `* 100` 改为秒到毫秒的 `* 1000`；不合并原 BC 提交的跨模块电源管理调用或锁状态接口。该提交已在本轮开始前由本地改写为 `[High Risk](not-complate)` 标记，保留现有版本，风险标记仍有效。

本批未改变 AC/BC 特有的统计上报能力及电池机路径。`confirm`、`relation_confirm` 未自动设置。

## 继续推进的 3 笔生产代码提交（到此暂停）

详细原始补丁和两侧行为见 CAP `docs/face_snapshot_converge_1010/batch7.md`。

20. `1e75e589`：依据 BC `d8eb1b19e`，共用 `fd_control_udsd_usr_add_face()` 的加锁后解锁出口，AC 的参数错误路径不再解未持有的锁。
21. `8bcb4a18`：依据 BC `0bb585cbc`，共用无效相似度重算、普通最高分的上界筛选、临时 JPEG 短写和特征更新失败后的释放；BC 熟人优先入口保持原样。此提交已在本轮开始前由本地改写为 `[Low Risk]` 标记，保留现有版本。
22. `fdb28d93`：依据 BC `49cc1cd51`，共用 face info 迁移回调返回值与有修改才写回的判断；AC/BC 的版本号和回调表保留各自配置。

这三笔均修改生产代码；此前已覆盖且无需修改的候选仍不计入本轮三笔。`confirm`、`relation_confirm` 未自动设置。

## 继续推进的 3 笔生产代码提交（到此暂停）

详细原始补丁、物理合并及保留差异见 CAP `docs/face_snapshot_converge_1010/batch8.md`。

23. `5de3d8be`：依据 BC `b9ede4035`，共用通知列表取消勾选后对每条 face info 的写回，AC 重启后可保留取消状态。
24. `b34d7f35`（`[Low Risk]`）：依据 BC `bceb7fbc8` 和 AC `0c090e6e7`，共用陌生人转熟人时写入前开启 `tmp_info.user_notify` 的逻辑；原后续赋值及容量处理保留。
25. `284535b2`：依据 AC `e69adae64f`、BC `99edff3d1a`，共用 50 项 FDS 队列容量定义，并将事件对象声明置于函数开头；队列读取和 IoT 报告流程保持原样。

这三笔均修改生产代码；`confirm`、`relation_confirm` 未自动设置。

## 第九批保留的 2 笔生产代码提交

详细原始补丁、物理合并和保留的产品差异见 CAP `docs/face_snapshot_converge_1010/batch9.md`。

26. `e84bb50f`：依据 AC `34bee47fb3`、BC `450a0bbeec`，共用 ringbuffer 事件非空检查及 `fd_control_notify_new_detection()` 调用；下游 AC/BC 处理不变。
27. `1ee05b0c`：依据 AC `34bee47fb3`、BC `d161ecab8a`，共用 HUB AI 配置监听及重载判断；AC 存储监听和 BC 电池统计监听的顺序保持原样。相关函数各宏组合的预处理结果与提交前一致。

原 `2f0fc518fcfea7d4b1742a1a5b3547335a170478` 涉及摄像头操作日志的跨模块能力，用户已从 CAP 分支删除；**暂缓，未合入**。`confirm`、`relation_confirm` 未自动设置。

## 继续推进的 3 笔生产代码提交（到此暂停）

详细原始补丁及物理合并依据见 CAP `docs/face_snapshot_converge_1010/batch10.md`。

28. `43bf37c2`：依据 BC `6b0eefe8e`，共用人形特征数量写回 `pdr_img_cnt`，修复 AC 上电加载人形数据时覆盖人脸图片数量的问题。
29. `bd2d47a7`：依据 BC `7e7c0f156`，删除 AC 新增人脸时先于 `fd_storage_add_face()` 的重复正式图片写入；保留后者的图片与 face info 保存。
30. `ded2a030`：依据 BC `be139db67`，共用可选调试 JPEG 的路径处理；AC 的额外检查及 `mkdir()` 分支移除，正常存储写入不变。

三笔均修改生产代码；`confirm`、`relation_confirm` 未自动设置。

## 第十一批复核：保留一笔，暂缓四笔

详细来源、物理合并依据及产品分支边界见 CAP `docs/face_snapshot_converge_1010/batch11.md`。

31. `5b309fb4`：依据 AC `34bee47fb3f416bfce4e17c0653280b98e18cd5b`、BC `450a0bbeeca02def4872e72949adcb95d33fa3b6` 及物理合并 `bb3085b88fbccd3b515d2ee7859417e807b7180f`，共用检测结果 `void *` 入口；内部仍按 PSS 开关转换结构类型。
32. `96929d1d`：记录以下四笔从 CAP 当前分支移除及其原始来源；仅修改审查文档。

原 `6daae2ae` 空人脸入口校验按用户要求暂缓，AC/BC 原判断不变。原 `ab524f8a` 只合了 BC `cd9bc9160cd18b212a5c5de17b5255db8aa58381` 的三处加载日志，遗漏同一原提交的 ringbuffer 回调、首次读取和启动日志；用户选择整笔暂缓，已撤回局部日志更改。该机制依赖 NVMP `libutils` 原提交 `54df1282d`；当前物理合并下 AC 宏展开不提供 `ringbuffer_attach_with_cb()`。原 `fa9b49ea` 关联 BC `bb3848b5598b600095f3665859111b6d59f7b9b6` 的场景特征新功能，原 `626817ec` 关联 BC `7a5ee0dfba0152e57e4f89dc6865a2ad1a608bde` 的最佳匹配新功能，均按用户要求暂缓，保留产品分支。

四笔旧 SHA 仅用于定位已移除提交，不代表当前 HEAD 已合入；`confirm`、`relation_confirm` 未自动设置。

## 第十二批：PSS 输入检查共用

`7b229a3c`：依据 AC `34bee47fb3f416bfce4e17c0653280b98e18cd5b`、BC `1403e6830e471144cf71112c23175731edee6025` 及物理合并 `bb3085b88fbccd3b515d2ee7859417e807b7180f`，共用 PSS 人数校验和零人脸转 `pss_process` 的原有入口；按用户复核，AC 的简单诊断日志也直接共用于 BC，第十一批暂缓的空人脸入口判断不动。AC 两种 PSS 配置及 BC 无 PSS 的完整函数与提交前 token 一致；BC 启用 PSS 时只增加该日志。详情见 CAP `docs/face_snapshot_converge_1010/batch12.md`。

## 第十三批：两笔源码提交及存储挂载修复复核

详细原始补丁及宏展开证据见 CAP `docs/face_snapshot_converge_1010/batch13.md`。

33. `c3d6c9d7`：依据 AC `34bee47fb3f416bfce4e17c0653280b98e18cd5b`、BC 基础 `450a0bbeeca02def4872e72949adcb95d33fa3b6` 与 BC `99edff3d1aea0e4eb6724d5ddffb63dd6d2820ae`，共用 HUB 配置状态变量声明；BC 的消息状态仍限 BC。
34. `c7f78f29`：依据 BC `1c851e9523057d6166204f99e78859a994527e2b` 的空宏块清理范围，删除 `face_control.c` 的七处空 `AC_ON_BC` 块与一处空 `BC_ON_AC` 块；八种 AC/BC、PSS、HUB 组合的整文件预处理输出逐字节不变，不将原提交其他子范围算作本笔完成。
35. `b437a05a`（`[Deferred]`）：完整复核 BC CAP `(1/2)` `08fd905b3a589373d76af5d46a5fd854a316d7c3` 及配套 NVMP `libutils` `(2/2)` `caa29a0f9475ef50cca472370a72dbfde2564025` 后，确认挂载等待与重挂载依赖电池机 `urdev=` 和配套提交公开的 `get_mnt_info()`；AC 使用固定设备的预初始化挂载且缺少该接口。整组标记暂缓跨入 AC，BC 原机制保留；撤销只共用声明和日志的旧本地 `6e89eab5`。此笔只写审查记录，不计作新生产代码合入。`cp()` 路径诊断仍由先前 `0ffe0983` 基于 AC #2 的合并覆盖。

本批两笔修改 CAP 源文件，其中空宏块清理没有运行时行为变化；一笔文档记录完整原提交的适用性。`confirm`、`relation_confirm` 未自动设置。

## 第十四批：保留两笔源码提交

详细来源、物理合并和宏展开证据见 CAP `docs/face_snapshot_converge_1010/batch14.md`。

36. `92e9ed68`：AC `98a66a726bd8182d1b2e84347eae5c4dc4472d20` 与 BC `450a0bbeeca02def4872e72949adcb95d33fa3b6` 都定义 `FD_FACE_NAME_LEN=32`；移除物理合并 `be46f651` 错误加上的 AC 专有宏，恢复 BC 头文件可见性，不改值或布局。
37. `c044bebe`：依据同两笔基础提交和物理合并 `bb3085b88fbccd3b515d2ee7859417e807b7180f`，共用相同人脸匹配时 BC 的详细诊断日志；BC 函数展开不变，AC 仅增加匹配人脸 ID 与索引的打印内容。
旧本地 `0a833bbe054f1736c6b5bd09cf336e3f95a12eed` 试图收敛周期报表的头文件路径、类型、枚举和函数声明。按用户复核，此笔缺少清晰的原始提交依据和合并边界，已从 CAP 分支撤销；AC/BC 原声明恢复，暂不计作第三笔完成的源码提交。若将来重审，需先明确原始提交逐项引入的接口、BC 电池机代理上报与 AC 本地周期上报的完整边界。

此前主机 26 项用例通过；撤销后差异空白检查通过。名称长度在 AC/BC 头文件展开均为 32；第二笔 BC 函数展开保持原样。未执行固件构建或设备验证；`confirm`、`relation_confirm` 未自动设置。

## FSS-LOG 状态

原本的第 5 笔 FSS-LOG 收敛提交 `10f72793918754815589060c004773d58c552541` 已整体回退。当前不修改 FSS-LOG，也不保留其测试和文档变更。后续如处理日志，`AC_ON_BC`、`BC_ON_AC` 必须分别判断，不能使用用户明确禁止的组合形式。

## 验证状态

- 当前 CAP 仓库运行 `python3 tests/face_snapshot/verify_batch1.py`：26 项测试通过。
- `git diff --check develop/bc_develop_220927 HEAD` 通过。
- 测试使用主机 GCC 和 fixture，覆盖 AC/BC 宏、优化宏、tag-only 更新、图片大小边界、分配失败及日志之外的已完成范围；不等于产品交叉编译、链接、设备、APP 或云端联调。
- 当前环境没有产品 `.config`、SDK staging/build 目录和交叉工具链，因此暂不宣称固件构建通过。

## 下一步入口

先收束 AC #1 已有配置证据；下一条主要源码线索是 AC #2 的七文件残余，之后闭环 AC #4 的通知链及 AC #7/#8 与 BC 物理整合的完整去向。按机制结合原始拓扑审查，已覆盖或暂缓来源保持原结论；完成度和具体边界见 [后续方向](mainline.md)。

