# face_snapshot 暂缓来源合入评审清单

本清单对应 [`merge_status.json`](merge_status.json) 在 2026-10-14 标记为 `deferred` 的 37 笔 AC/BC 原始提交。这里的“待评审”表示需要判断**是否跨侧合入**；暂缓不等于原分支功能缺失。原提交 SHA、标题、作者日期和改动文件数取自 CAP Git 历史；文件数统计整笔提交，括号内仅列 `face_snapshot` 焦点文件。风险是跨侧迁移的初评，尚非测试结论。状态和合入结果仍以 `merge_status.json` 为准。

评审时优先成组处理带 `(1/2)`、`(2/3)`、`[3/5]` 等编号的提交，并核对 NVMP、AVTS、NSD、配置与消息消费者。确认适用后再建立源码修复提交及多对多来源关系；不因目标 BC 路径已有代码，就直接判定 AC 路径可用。

## AC 来源：9 笔

### AC#5 · 日志接口宏

- 原提交：`906e6b5edc7eda219ddfa55d3fd4e63fe6b4d836`，2024-12-17，`[all] cap:调整日志接口宏定义适配日志分类(3/4)-patch`；CAP 1 文件（`face_storage.h`）。
- 功能：调整 FSS 存储头文件的日志接口宏，接入分类日志系列。
- 风险：**中**。日志宏的定义与调用跨模块；此前本地 FSS-LOG 收敛已撤销。评审整套 `(3/4)` 接口及两侧编译宏后再决定是否重做。

### AC#6 · 厂商名称

- 原提交：`3f74974b9241be9e969b827a5b18f04365e18c73`，2025-06-04，`[all]change manufacturer name in NVMP platform code`；CAP 131 文件（`face_control.c/.h`、`face_feature.c/.h`、`face_storage.c/.h`、`fss.c`）。
- 功能：统一源码版权头中的厂商名称。
- 风险：**低**。主要是文本变更，但属于跨模块批量改名；核对目标六个 `face_*` 文件与全 CAP 命名口径后整笔处理。

### AC#9 · 随机数源

- 原提交：`12f602f96c52f1906d4baa5d0413f8dd59567ba7`，2025-06-05，`[all] nvmp:  replaces the standard C library random number generator (3/4)`；CAP 6 文件（`face_control.c`）。
- 功能：把人脸控制中的随机数调用纳入平台随机数替换系列。
- 风险：**中**。随机源、链接依赖和跨模块调用都需与系列其余提交一致；旧本地 `71b47a19` 已移除，评审后才能恢复。

### AC#15 · 旧图片配置迁移

- 原提交：`91713aef6e078ddf179afca70ea060bcfaf9fe6b`，2026-01-10，`[CAP]face_control:fix face_snapshot config[1/2]`；CAP 2 文件（`face_control.c`，另有 Makefile）。
- 功能：通过 `FIX_FSS_PIC_CFG` 关闭既有持久配置中的 `save_pic`，修正图片保存开关。
- 风险：**中**。目标保留修复函数，但 Makefile 未启用宏；默认配置为 off 不等于已迁移旧设备。评审配套 `(2/2)`、产品宏和升级时机。

### AC#17 · HUB 人脸告警代理

- 原提交：`2900128f10da10f075a1953a1ed814834f38dec9`，2026-01-21，`[all] avts: fixed the issue where the iot message of hub_storage proxy lacked faceid, name, and alias fields, resulting in the failure of pushing iot for face events [1/2]  avts : 修复hub_storage代理的iot消息缺少faceid、name、alias字段导致人脸事件推送iot失败的问题[1/2]`；CAP 1 文件（`face_control.c`）。
- 功能：HUB 绑定时将带 `faceid`、`name`、`alias` 的人脸告警交给 hub_storage 代理。
- 风险：**高**。发送端、AVTS/hub_storage `(2/2)` 消费端和云端消息格式必须一致；目标 AC 发送路径虽在，BC 跨侧适用性未证实。

### AC#21 · libfss 回调注册

- 原提交：`7bbf5e9a4a9f18aebe036de8832339ed2533def2`，2026-04-17，`[cap]fss:fix compile error and standardize code`；CAP 2 文件（`face_control.c`）。
- 功能：注册三项 libfss 回调，修复并规范人脸模块接口。
- 风险：**高**。目标 AC 路径已有、BC 路径没有；提交说明关联 CAP/NVMP/AVTS/NSD。评审回调 ABI、链接库和消费者后再跨入 BC。

### AC#26 · 人脸遥测

- 原提交：`1ab529891045131033eef8f7e2b625932f15d02e`，2025-11-07，`[ALL] telemetry:telemetry support face recognition(2/3)`；CAP 2 文件（`face_control.c/.h`）。
- 功能：采集人脸识别统计并提供 `getFaceTelemetryInfo`。
- 风险：**中**。目标 AC 路径已有，BC 未启用；NVMP `(1/3)` 为 `369f7ce4520c154095c26ec647cb07c5acdc8c85`。评审剩余消费者、产品开关和遥测数据契约。

### AC#28 · 摄像头操作日志

- 原提交：`dd2600fb397771d69ddfb4d7b41484f6e6f07ca9`，2026-05-14，`[Models with CAMERA_OPERATION_LOG_SUPPORT] cap:Add camera log (3/4)`；CAP 26 文件（`fss.c`）。
- 功能：在含 `CAMERA_OPERATION_LOG_SUPPORT` 的机型中补充摄像头操作日志。
- 风险：**中**。涉及 26 个模块及日志消费者；旧本地 `2f0fc518` 已移除。评审产品开关与整套 `(3/4)` 日志格式。

### AC#29 · 预设方法日志

- 原提交：`14378dec6d5e43e7deec71e79d9d732a71f1bdbb`，2026-08-10，`[Models with CAMERA_OPERATION_LOG_SUPPORT] cap: modify pre_set method(2/2)`；CAP 16 文件（`fss.c`）。
- 功能：调整预设方法相关处理，配合摄像头操作日志系列。
- 风险：**中**。与 AC#28 的日志能力和跨模块 DS 接口相关；需先核对 `(1/2)` 及目标机型再评审合入。

## BC 来源：28 笔

### BC#5 · 最佳匹配接口

- 原提交：`7a5ee0dfba0152e57e4f89dc6865a2ad1a608bde`，2025-06-26，`[all] fss|face_snapshot: Add support for finding best match function interface(2/2)`；CAP 2 文件（`face_control.c`、`face_storage.h`）。
- 功能：增加人脸特征最佳匹配接口，供外部查询匹配结果。
- 风险：**高**。新增接口改变匹配结果对外含义；用户此前要求暂缓。评审 `(1/2)` 消费者、陌生人返回值及阈值行为。

### BC#6 · AOV 休眠前保存

- 原提交：`26843acc363708ee4975ef04a9b87b23215a60ec`，2025-06-12，`[all]cap:save face data before AOV`；CAP 2 文件（`fd_statistics.c`，另有 `battery_manage/power_down.c`）。
- 功能：休眠前保存人脸统计，并调整定时器与锁顺序，避免 AOV 并发死锁。
- 风险：**高**。牵涉电源关闭时序和跨模块调用；AC 没有同一电池机休眠入口。评审休眠链和锁顺序后整笔处理。

### BC#7 · 熟人优先匹配

- 原提交：`b49a124e00f5f79db64923bb3ad6d164068b0879`，2025-07-04，`[all] face_snapshot: prioritize adding familiar face,when the same person is in both group`；CAP 1 文件（`face_control.c`）。
- 功能：相似度遍历遇到超过同人阈值的熟人时提前选定该熟人。
- 风险：**高**。AC 当前按最高分选择；跨侧会改变人脸归属。评审同组熟人/陌生人并存及阈值边界。

### BC#10 · 电池机周/月统计

- 原提交：`fcda83d10c63d9ee7a64d7fd6f487eb692d146e7`，2025-07-16，`[all] face_snapshot: IoT Wi-Fi Monthly/Weekly FD Statistics (2/4)`；CAP 6 文件（`face_control.c`、`fd_statistics.c/.h`、`fd_statistics_stg.c/.h`）。
- 功能：为电池机生成并上报人脸识别周/月统计。
- 风险：**高**。用户已定为 AC/BC 固有产品差异，不能用 AC 周期报表替代。评审整套 `(2/4)`、Wi-Fi 上报与持久化契约后才考虑变更决定。

### BC#14 · 人脸时间换算

- 原提交：`285018e33f5d633df02e7d24621432b0e78b0af4`，2025-08-19，`[all]face snapshot: fix face utc time incorrect problem`；CAP 1 文件（`face_control.c`）。
- 功能：用 MCU 开机时间将电池机 RTOS 阶段的相对时间换算为 UTC。
- 风险：**高**。AC 直接使用 `utc_start`，未证实有同类时间源；错误跨入会使事件时间偏移。须连同 BC#16 的等值边界审查。

### BC#16 · 时间换算边界

- 原提交：`96438c16882e200327e93e317dc4d4451ba36667`，2025-11-21，`[all] face_snapshot: Fix Incorrect Face Result Timestamp`；CAP 1 文件（`face_control.c`）。
- 功能：修正 BC#14 换算中 `utc_start == start_time` 的边界，避免重复加上开机时间。
- 风险：**中**。依赖 BC#14 的时间模型；不应脱离该转换独立迁入 AC。

### BC#17 · 陌生人推送阈值

- 原提交：`645eb8f0acaafdb55b06f81b0c0801191432b3db`，2025-08-05，`[all]face snapshot:face detect msg push when upto push threshold(1/2)`；CAP 4 文件（`face_control.c/.h`、`fd_statistics.c`、`fss.c`）。
- 功能：把陌生人出现次数持久化，并结合唤醒后的推送阈值决定是否告警。
- 风险：**高**。改变推送次数、时机及 flash 写入；NVMP `(2/2)` `764b4d966` 增加 `FSS_MSG_PUSH` 模型。评审 AC 的 60 秒静默策略与消息消费者。

### BC#18 · ringbuffer 回调附着

- 原提交：`cd9bc9160cd18b212a5c5de17b5255db8aa58381`，2025-11-12，`[All] cap/fss: use callback to attach ringbuffer instead of timer retry (2/2)`；CAP 1 文件（`face_control.c`）。
- 功能：用 ringbuffer 创建回调触发附着，替代定时重试。
- 风险：**高**。AC 侧 NVMP `libutils/ringbuffer_attach_with_cb()` 依赖未齐；用户明确要求整笔暂缓。评审 `(1/2)`、回调生命周期和首次附着时序。

### BC#22 · 休眠前事件索引

- 原提交：`95abd9522ccadcc3f6250f159213a2bd73e74ad5`，2025-10-20，`[all]face_snapshot: save face index when the face keeps appearing in front of the camera before power down(2/2)`；CAP 2 文件（`face_control.c`，另有 `battery_manage/power_down.c`）。
- 功能：休眠前同步人脸事件索引，并调整事件起始时间。
- 风险：**高**。依赖 AVTS `(1/2)`、电池机休眠链和视频索引契约；目标 AC 无同一 `fss_events_sync` 调用。评审整组后迁移。

### BC#24 · 自适应 IQA

- 原提交：`ea1f1e58e27219d43e466ec8c5c06d2e9006d6bc`，2025-11-11，`[all] fss | face_feature: add fss adapt iqa_thresh (2/2)`；CAP 3 文件（`face_feature.c/.h`、`fss.c`）。
- 功能：增加低角度/高模糊度的备选人脸质量门槛及 AMS 配置字段。
- 风险：**高**。影响人脸入库筛选与 DS 数据模型；NVMP `(1/2)` `e73752f1ba1a9c61db52f36c722d52a0d651afb5`。评审 AC 算法分数分布和字段兼容。

### BC#25 · 模型更新后重算特征

- 原提交：`0bb947224bc08bdfc400aaa353d437f29e573e64`，2026-02-26，`[FSS] Recalculate face features when face recognition model is updated (2/3)`；CAP 2 文件（`face_control.c`、`fss.c`）。
- 功能：比较模型 MD5，在 DLA 可用时重算库中人脸特征并记录新版本。
- 风险：**高**。会重写特征数据并影响识别可用性；原说明限定 D260v1，NVMP `(1/3)` `a7adeb41dd9a0cfee39edb989b8845a47ab89911`。评审 `(3/3)`、重试和断电恢复。

### BC#26 · 熟人匹配入口

- 原提交：`bad5f512f868b751170c565d1abd90bf5cde1b62`，2025-12-24，`[all] cap|face_snapshot: feature matching func is valid for familar`；CAP 1 文件（`face_control.c`）。
- 功能：让最佳匹配接口对熟人结果生效。
- 风险：**高**。与 BC#5 同一新接口，涉及陌生人/熟人返回语义；应与 BC#5 成组评审。

### BC#28 · 人脸大小质量门槛

- 原提交：`8afda7b47cc26866765f0cd081f65a428a1a6da3`，2026-03-06，`[FSS] Add filter conditions for size score(2/2)`；CAP 3 文件（`face_feature.c/.h`、`fss.c`）。
- 功能：增加 `size_score` 阈值，过滤尺寸质量不足的人脸。
- 风险：**高**。影响入库率和 IQA 字段兼容；NVMP `(1/2)` `90e10a321fa7c55ee4315da48e2421625e041b67`。评审 AC 分数来源和阈值配置。

### BC#35 · PDR 容量缩减

- 原提交：`caab424ca6830e1250f42ebf36686eba8c9ef0fd`，2026-03-23，`[All] cap/pss: reduce max person_num and max person snapshot size`；CAP 1 文件（`pss_enhance/pdr_storage.h`）。
- 功能：把 PDR 图片空间从 40K 调为 20K，人物记录数调为 `FD_FACE_SUPPORT_NUM`，每人图片占位调为 5。
- 风险：**高**。改变持久存储容量/布局；AC 仍使用 40K/100/10。评审已有数据迁移、容量峰值和产品配置。

### BC#38 · 分包上传人脸

- 原提交：`1a03e63298ff39ec1b1890dce4999fea31322b10`，2026-04-27，`[all] face_control: Support doFaceInfoAddPacketized API (1/2)`；CAP 2 文件（`face_control.c`、`fss.c`）。
- 功能：增加大图片分包上传 `doFaceInfoAddPacketized` 接口。
- 风险：**高**。新增对外 DS API；NVMP `(2/2)` `b4b44c924be1b804889147c764942f81e3df1d9c` 负责 libds 映射和大小字段。评审 AC 传输需求、分包状态机与消息体限制。

### BC#42 · 电池机挂载数据保护

- 原提交：`08fd905b3a589373d76af5d46a5fd854a316d7c3`，2026-05-21，`[all] fss: fixed face data lost (1/2)`；CAP 1 文件（`face_storage.c`）。
- 功能：修正人脸存储挂载/读取时序造成的数据丢失。
- 风险：**高**。与 NVMP `caa29a0f` 电池机挂载系列相关；评审挂载失败、重试及存储版本后整组处理。

### BC#43 · DS 接口安全模板

- 原提交：`ea33fe4d4a27504ed9284dc8bd5daead504c6bca`，2026-05-15，`[CAP] Security Optimization for DS Interface (3/4)`；CAP 69 文件（`face_control.c`、`fd_statistics.c`、`fss.c`）。
- 功能：为 DS 接口登记访问校验模板，限制未授权调用。
- 风险：**高**。8 项普通人脸接口及统计/配置模板当前已共用；分包上传模板仍仅在 BC 路径，依赖 BC#38。整笔还跨 69 模块；继续评审 `(1/4)` 至 `(4/4)`、权限表及兼容客户端。

### BC#44 · 场景感知特征更新

- 原提交：`bb3848b5598b600095f3665859111b6d59f7b9b6`，2026-04-15，`[ALL] face_snapshot: add scene-aware real-time feature update for familiar faces`；CAP 5 文件（`face_control.c`、`face_feature.c/.h`、`face_storage.c/.h`）。
- 功能：按光照场景实时更新熟人人脸特征，并保存场景标记。
- 风险：**高**。改变识别库内容和存储格式；用户此前要求暂缓。评审场景切换、旧库兼容及更新失败恢复。

### BC#47 · 增强包裹检测

- 原提交：`7012ac55e8970c87146e8e5f740454d2c4d84350`，2026-07-03，`[all]cap: support enhanced package detection [2/5]`；CAP 30 文件（`face_control.c`）。
- 功能：建立增强包裹检测模块，并在 `EN_PKGD_SUPPORT` 下转发人脸结果。
- 风险：**高**。跨电源、MCU、告警等模块及 NVMP `(1/5)` `16d21a671d5d3332c47c33b5e662ad3d2973d914`；评审整套 `[1/5]` 至 `[5/5]` 与 AC 产品适用性。

### BC#50 · 包裹历史与人脸事件

- 原提交：`6bf25ceb87ec8e0967db1f54f6802149f3e38d79`，2026-07-06，`[cap] en_pkgd|face_snapshot: update package history when face detected (1/2)`；CAP 3 文件（`face_control.c`）。
- 功能：在人脸检测时更新本地包裹历史，并调整人脸 IoT 告警 `pushable`。
- 风险：**高**。依赖包裹历史模块、云端消费者及另一半系列；与 BC#47、BC#51 成组评审。

### BC#51 · 包裹历史产品开关

- 原提交：`b8e8a80294fc5f063c82dffb2f4d4620f4e5baeb`，2026-07-22，`[cap] en_pkgd: add macro control for local package history maintainance logic`；CAP 5 文件（`face_control.c`）。
- 功能：用 `LOCAL_PKG_HISTORY_SUPPORT` 控制本地包裹历史维护。
- 风险：**中**。依附 BC#47/#50，跨 en_pkgd、hsr 和人脸模块；评审产品宏组合与未启用时的消息行为。

### BC#52 · NAND 打包与电池分支兼容

- 原提交：`3ec3c0ef990abb98e4b4afa30070c6f5fe7cda9e`，2026-06-17，`[ALL] CAP|cap: Fix NAND firmware packaging and add battery cam branch compatibility [3/5]`；CAP 17 文件（`face_control.c`、`fd_statistics.c`）。
- 功能：迁移 NAND 固件打包逻辑，并用产品宏适配常电/电池分支编译。
- 风险：**高**。影响 Makefile、17 个模块及产品构建矩阵；目标人脸路径已有兼容片段。评审整套 `[1/5]` 至 `[5/5]` 和实际产品宏。

### BC#53 · 模块化日志初次引入

- 原提交：`a8aed44ebc4b24f0cc45584ad64f1eba52edac21`，2026-07-10，`[ALL] CAP|log : adapt module-based logging and unify msg_debug interface[3/4]`；CAP 65 文件（`face_storage.h`）。
- 功能：切换模块化日志并统一 `msg_debug` 接口。
- 风险：**中**。跨 65 文件且有后续回退/重提；旧本地 FSS-LOG 已整体回退。与 BC#56/#57 和 AC#5 成组评审最终版本。

### BC#56 · 模块化日志中间回退

- 原提交：`03c33af88e5fdf6302bebcce676e9a0081ed3d2f`，2026-07-28，`Revert "Merge "[ALL] CAP|log : adapt module-based logging and unify msg_debug interface[3/4]" into develop/bc_develop_220927"`；CAP 65 文件（`face_storage.h`）。
- 功能：回退 BC#53 的中间日志版本。
- 风险：**中**。这是历史状态转换，不应孤立重放；与 BC#53/#57 比较最终代码和宏定义。

### BC#57 · 模块化日志重提

- 原提交：`8f72dafca02825230827e9c2f212a3fd833bbb45`，2026-07-30，`[ALL] CAP|log : adapt module-based logging and unify msg_debug interface[3/4]`；CAP 65 文件（`face_storage.h`）。
- 功能：在回退后再次引入模块化日志适配。
- 风险：**中**。需以重提后的最终接口为基准，同时核对 AC#5 和全 CAP 依赖；此前局部本地收敛已撤销。

### BC#59 · HUB 告警代理字段

- 原提交：`48e74a2785dc75597636ea35f1e8e7d180036d5c`，2026-08-24，`[all] face_control: include HUB fields for familiar and unfamiliar recongition events`；CAP 1 文件（`face_control.c`）。
- 功能：根据 HUB 存储/AI 状态，在熟人、陌生人告警 JSON 中加入 `msgAgent`。
- 风险：**高**。改变消息协议；AC 告警 JSON 没有该字段。评审 HUB 代理消费者及 AC#17 的发送链。

### BC#63 · 分包上传编译声明

- 原提交：`13f832c751368d15618ae7d9209634f6657d7429`，2026-09-14，`[CAP] face_control: fix compile error`；CAP 1 文件（`face_control.c`）。
- 功能：给分包上传路径中的两个函数补前置声明，修复编译顺序问题。
- 风险：**低**。修复本身是声明；是否迁入 AC 取决于 BC#38 及 NVMP 配套接口是否引入，应成组评审。

### BC#65 · PSS 合格人脸标签

- 原提交：`3e40aa2606ea54ff93f9b39deeddb7cd970d351b`，2026-08-28，`[all] face_control: add qualified face tags for pss recognition`；CAP 1 文件（`face_control.c`）。
- 功能：扩展 PSS 多人选择、熟人匹配和合格人脸事件/视频标签。
- 风险：**高**。影响识别选择、PSS 存储及视频事件消费者；评审 AC 对应算法与消息契约后再考虑迁移。
