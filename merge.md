# cd_alarm 合并口径
仓库： NVMP/nvmp/tp_package/cap


## 原始提交基线与责任

- 同步目标分支：`bc_merge_0915`，基于 `secure/bc_merge`。
- 常电原始分支：`develop/nvmp_release_1.9.2`。
- 电池原始分支：`develop/bc_develop_220927`。
- 当前共同祖先：`af14c8cbad7af217cfe0dc7704bb8f63d8797fdd`。
- 合并以共同祖先后的原始提交为责任单位，而不是以最终文件 diff 或某一边的最终代码为单位。

## 同步流程

目标是尽可能消除 `AC_ON_BC`、`BC_ON_AC`；它们仅用于无法统一的真实平台或协议差异。

合并来源只能是常电原始分支和电池原始分支的提交；不得以其他合并分支、临时整合分支或其提交作为功能来源。

1. 对两个原始分支分别列出从共同祖先开始的独特提交，并按提交顺序建立来源清单。
2. 扫描本文件夹下的文件，逐处找出 `AC_ON_BC`、`BC_ON_AC`，并按函数、调用点和功能域建立清单。
3. 对清单中的每一处条件编译，分别在常电分支和电池分支追溯引入该差异的原始提交，确认其引入背景、影响范围及依赖。
4. 若一侧提交实现的是另一侧缺失的功能、逻辑，则以该原始提交为依据，将其实际改动及关联调用链直接合入对方；合入后收敛或删除对应的 `AC_ON_BC`、`BC_ON_AC`。
5. 对仍不能合并的差异，记录平台/协议原因、对应原始提交和保留范围，且将条件编译缩小到最小必要代码块。
6. 每完成一个原始提交，在来源清单中记录同步提交号、冲突处理与验证结果，再处理下一个原始提交。

## 功能迁移原则

- 合并方向由原始提交决定：先确认常电或电池哪一侧引入了目标功能/逻辑，再将该提交的真实语义迁入另一侧；不得为了“看起来共用”而重新设计两侧实现。
- 先按函数和调用关系识别常电/电池差异的真实原因：数据模型、消息协议、外部能力、运行策略或多通道。
- `AC_ON_BC`、`BC_ON_AC` 只能保留真实的平台/协议差异，不能作为“常电功能不迁电池”的隔离手段。
- 能抽成公共流程的内容直接共享：参数检查、状态索引、区域事务、定时器、重发与状态清理。
- 确有不同的消息结构、外部模块能力或电池专属策略时，保留最小差异分支；不要复制整函数。
- 禁止仅为消除条件编译而新增中间适配层、包装函数、参数化接口或状态抽象。只有原始提交本身包含该抽象，或迁入其完整调用链确实必需且可追溯到原始提交时，才允许新增。
- 每次合入以一个原始提交的关联链为边界：实现、直接调用点、回调、定时器、状态与数据模型必须同时处理；不能只抽取其中的局部公共片段。
- 不新增用于包裹整段功能的总开关（例如 `CD_MULTI_CHANNEL_SUPPORT`）。

## 多通道示例

- 多通道的功能开关是 `DUAL_ALGO_ENABLE`：单通道使用 `IPC_CHANNEL_1`，双通道完整处理 `IPC_CHANNEL_1`、`IPC_CHANNEL_2`。
- 该示例同样适用于其他功能：任何功能迁移都必须沿实现、调用点、状态、数据模型和外部依赖完整闭环。

## 提交规则

一个同步提交必须对一个原始提交（或明确标注的子范围）负责，并且是可独立理解、可编译的功能单元，且包含：

1. 被修改函数的实现；
2. 该函数所有模块内调用点、回调和定时器入口；
3. 受影响的数据结构、状态索引或 DS 数据模型；
4. CAP 外的依赖点以 `TODO bc_merge: ...` 写在触发位置。

禁止只修改函数签名而不同时更新调用点；禁止把 release 的整段 diff 直接导入后再拆；禁止提交无法到达第二通道的半成品。

提交信息或提交正文必须写明：`source: <原始分支>/<原始提交>`、功能范围、冲突决策和 CAP 外 TODO。

## 函数关系与合并顺序

先按差异来源建立函数族，再按依赖顺序提交；下列多通道相关函数族只是当前首批示例。其他常电/电池分歧也按相同规则拆分。

### 1. 区域事务与双路请求（原子提交）

`add_cd_regions`
→ `cd_region_check`
→ `init_recover_context(…, chn_id)`
→ `init_add_context(…, param, chn_id)`
→ `del_cd_table(chn_id)`
→ `ds_handle`
→ `cd_region_restart`

- 单路请求读取 `region_info`。
- 双路请求读取 `"1"`、`"2"`；第二路的校验、备份、删表、写入、失败恢复必须完整迁入电池侧。
- 这组提交还需覆盖 `CD_REGION_INFO_LIST_NAME_CHN2`、`CD_REGION_INFO_PATH_PREFIX_CHN2`、`CD_REGION_INFO_NAME_PREFIX_CHN2` 的选择。
- CAP 外 TODO：AMS/VDR 必须按 `VDR_CD_RELOAD_MSG.chn` 重载对应通道区域。

### 2. 检测状态与报警入口（原子提交）

`cd_alarm_occur_callback`
→ `cd_alarm_occur`
→ `cd_alarm_start_effect` / `cd_alarm_end_effect`
→ `cd_alarm_resend`

- `g_cd_detec`、`g_cd_status` 按通道维护，状态索引统一为：
  `status_idx = type + chn_id * CD_ALARM_LAST`。
- 算法上报的 `CD_RESULT.chn` 必须被校验并用于状态、开关、重发和结束定时器。
- CAP 外 TODO：电池 VDR 必须在 `AMS_VDR_CD_CROSS_LINE` 消息中填充 `CD_RESULT.chn`。

### 3. 联动消息与录像（原子提交）

`cd_msg_send_start`
→ `cd_msg_send_stop`
→ `cd_send_msg_push`
→ `cd_alarm_resend`

- 录像 `EVENT_CHANGE_MSG` 必须携带并消费 `chn`；每一路独立维护录像状态。
- 对不携带通道的声、光、ONVIF 等公共联动，先通过“任一路仍在 processing”判断，避免其中一路结束时错误发送全局 stop。
- 推送 JSON 需保留 `chn_id`。
- CAP 外 TODO：录像模块按 `EVENT_CHANGE_MSG.chn` 隔离状态；告警投递链路保留 `chn_id`。

### 4. 配置重载、启动停止与数据模型（原子提交）

`cd_update_enabled`
→ `cd_alarm_reload`
→ `cd_restart(chn_id)`
→ `cd_alarm_start` / `cd_alarm_stop`
→ `cd_alarm_main` / `linecrossing_detection_data_model`

- 双路读取 `CD_DETECTION_PATH_CHN2`，数据监控、API、表定义和区域表必须同时暴露第二路。
- 第二路重载使用 `VDR_CD_RELOAD_MSG.chn = IPC_CHANNEL_2`。
- `CAM_CAPABILITY_PATH` 的 `chn_with_ptz` 决定每一路 PTZ 抑制逻辑。
- CAP 外 TODO：能力提供方输出逐通道 PTZ 能力；AMS/VDR 消费重载通道号。

## 验收

- 每个提交后：`git diff --check`、检查该函数所有调用点的参数与索引。
- 双路构建至少验证：区域设置（仅 1、仅 2、1+2）、第二路检测开关、第二路事件触发/停止、录像和推送通道归属。
- 单路电池行为保持使用 `IPC_CHANNEL_1`，不得因双路迁移改变原有接口或状态语义。
