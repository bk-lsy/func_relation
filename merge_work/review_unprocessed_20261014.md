# face_snapshot 未处理来源复核（2026-10-14）

目标 CAP `face_snapshot_converge_1010`：`785e753721f12b5b9712cec319e8d9e9cf9114ea`。本轮按原始补丁核对六笔此前标为 `no_merge_fix` 的来源，没有修改 CAP 源码；逐笔动态状态以 [`merge_status.json`](../branch_diff/face_snapshot/merge_status.json) 为准。

| 来源 | 原补丁与目标证据 | 处置 |
| --- | --- | --- |
| AC #27 `ebb0da210c6c5270f059715b454b2b64328ce82c` | 原补丁修改 `face_control.c/.h` 的遥测宏结束注释、空参返回 `SLP_EINVARG`、`getFaceTelemetryInfo` 注册保护。目标 AC 路径逐项保留，`git blame` 指向 BC 物理整合 `bb3085b88fbccd3b515d2ee7859417e807b7180f`。 | 本笔焦点修复已有覆盖；AC #26 的遥测跨仓系列另审。 |
| BC #6 `26843acc363708ee4975ef04a9b87b23215a60ec` | 原提交同时改 `battery_manage/power_down.c` 与 `fd_statistics.c`：AOV 休眠前保存人脸数据，保存前删除定时器以避开持锁冲突。目标 BC 路径保留；AC 路径没有同一电池机休眠调用。 | 跨模块电源时序未闭环，整笔暂缓跨入 AC。 |
| BC #13 `22c12edfc09bcceee973ccdfafc30a90436f57cb` | 原补丁只删除 `fss_data_model()` 的启动分隔线 `printf`；AC tip、BC 基础和目标均无此打印。 | 已有覆盖。 |
| BC #38 `1a03e63298ff39ec1b1890dce4999fea31322b10` | CAP `(1/2)` 增加电池机 `doFaceInfoAddPacketized`；NVMP `(2/2)` `b4b44c924be1b804889147c764942f81e3df1d9c` 同时增加 libds API 映射和 libsdm `max_faceinfo_bytes`。NVMP BC ref 含配套，AC 对照 ref 无这两项；CAP 目标包上传仅在 BC 路径。 | 暂缓跨入 AC；保留 BC 实现。 |
| BC #49 `e933738e1f6b75a20eb2323aa0796c04fa1194f0` | 原补丁把月报中对 NULL `rep_infos` 的 `memset` 改回 `calloc`。目标经物理整合 `f96c42168ed1262f07bb1afb6240645ad4e24ff6` 使用零初始化的 `fds_report_status rep_infos[32]`；月报 `memset` 操作有效数组。 | 原空指针问题已有覆盖；不修改 BC #10 的暂缓决定。 |
| BC #63 `13f832c751368d15618ae7d9209634f6657d7429` | 原补丁只增加 BC 包上传的两个函数前置声明；目标 BC 路径已有声明，AC 路径没有相应 API/函数。 | 随 BC #38 和 NVMP `(2/2)` 暂缓跨侧合并。 |

本轮是源级补丁覆盖和依赖判断，没有固件或设备验证；未将已有覆盖计成新的本地源码合入提交。
