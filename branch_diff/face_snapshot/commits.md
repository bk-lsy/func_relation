# face_snapshot 焦点提交实际补丁索引

基线：CAP AC `178f33f6da6a70893faecea14b1b51ef64bc62ac`，BC `3e40aa2606ea54ff93f9b39deeddb7cd970d351b`。按 `git rev-list --full-history --reverse --topo-order --no-merges <opposite>..<side> -- src/modules/face_snapshot` 排序。每行文件由 `git show --format= --numstat <SHA> -- src/modules/face_snapshot` 取得；增删行仅供定位，不代表行为等价或刚需。`N.0` 仅为本快照阅读编号。

缩写：`ctl`=face_control，`fea`=face_feature，`stg`=face_storage，`stat`=fd_statistics，`stat_stg`=fd_statistics_stg，`ver`=fd_stg_version，`pss`=pss_enhance，`cfg`=files 或 files_ac；未缩写的名称保持原样。

## AC 物理独有焦点提交（30）

| 编号 | CAP 完整 SHA | 提交标题 | 路径内文件与行数 (+/-) |
| --- | --- | --- | --- |
| 1.0 | `531e61624272f64fb8e0d0fc09af286e6f52a180` | [all] cap\|face_snapshot: support face_snapshot data model | Makefile 19/0, cfg/arming_schedule 11/0, cfg/feature_code 6/0, cfg/fss_gen_cfg 14/0, cfg/fss_pic_cfg 8/0, cfg/fss_rule 9/0, cfg/fss_size_cfg 9/0, cfg/region_info 13/0, cfg/size_limit 9/0, cfg/storage_head_info 14/0, fss.c 297/0 |
| 2.0 | `98a66a726bd8182d1b2e84347eae5c4dc4472d20` | [all] cap\|support face_recognition | ctl.c 2648/0, ctl.h 130/0, fea.c 693/0, fea.h 151/0, stg.c 1295/0, stg.h 243/0, fss.c 55/0 |
| 3.0 | `1df1db390256664982d7122ee31bac45d4b9b74d` | [all] cap\|face_snapshot: support only change tag | ctl.c 2/2 |
| 4.0 | `0c090e6e760c94ae5fba13ce346c735a24df99e3` | [all] cap\|face_snapshot: support notify and send image to APP | ctl.c 122/18, ctl.h 2/0, fss.c 3/1 |
| 5.0 | `906e6b5edc7eda219ddfa55d3fd4e63fe6b4d836` | [all] cap:调整日志接口宏定义适配日志分类(3/4)-patch | stg.h 1/1 |
| 6.0 | `3f74974b9241be9e969b827a5b18f04365e18c73` | [all]change manufacturer name in NVMP platform code | ctl.c 1/1, ctl.h 1/1, fea.c 1/1, fea.h 1/1, stg.c 1/1, stg.h 1/1, fss.c 1/1 |
| 7.0 | `34bee47fb3f416bfce4e17c0653280b98e18cd5b` | [ALL] cap: merge commit from nvmp_release_1.8_sz_250116_face_detection to other branch(CAP:1/2) | Makefile 12/1, ctl.c 1480/182, ctl.h 75/7, fea.c 217/20, fea.h 48/12, stg.c 133/143, stg.h 15/15, stat.c 1394/0, stat.h 150/0, stat_stg.c 1417/0, stat_stg.h 273/0, ver/ver.c 168/0, ver/ver.h 31/0, cfg/fss_rule 1/1, cfg/storage_head_info 1/1, fss.c 145/0, pss/pdr_storage.c 210/0, pss/pdr_storage.h 112/0, pss/recog_img_stg_version.c 97/0, pss/recog_img_stg_version.h 47/0, pss/recog_img_storage.c 1233/0, pss/recog_img_storage.h 142/0, ring_object.c 125/0, ring_object.h 69/0 |
| 8.0 | `747e518a37f12c26f4ea872e98a8d3a7363aad4c` | [ALL] cap: merge commit from nvmp_release_1.8_sz_250116_face_detection to other branch(CAP:2/2) | ctl.c 45/33, fea.c 2/2, fea.h 21/6, stg.c 8/8, stat.c 24/17, stat.h 1/1, stat_stg.c 47/15, stat_stg.h 2/2, pss/recog_img_storage.c 143/105 |
| 9.0 | `12f602f96c52f1906d4baa5d0413f8dd59567ba7` | [all] nvmp:  replaces the standard C library random number generator (3/4) | ctl.c 2/2 |
| 10.0 | `0f8c7c9dfceb407df8e8f49ea3d38edf57738943` | Revert "[all]cap:turn off camera face detection when bound to face support hub" | ctl.c 1/44 |
| 11.0 | `1f57bf37ec82e735e13b0909d98080a9a7e4407e` | [all] cap: change face_snapshot config fss_pic_cfg/save_pic to off | cfg/fss_pic_cfg 1/1 |
| 12.0 | `94aef932ffa51fbac9d0cb63aab6e5d69ebc2f1b` | [All] fss: Fix incorrect close file descriptor 0 and file descriptor leaks | stg.c 4/10 |
| 13.0 | `e69adae64faf5b6f1d77e897f054e7d81effe9dc` | [cap]face_snapshot:fix some bugs of face snapshot | ctl.c 149/62, stat.c 5/2, stat.h 2/1 |
| 14.0 | `de1da536532c73b82b23210e732aec72ee0efc04` | [cap]face_snapshot:fix the issue introduced by the submission of 1cfaf2 | ctl.c 33/24 |
| 15.0 | `91713aef6e078ddf179afca70ea060bcfaf9fe6b` | [CAP]face_control:fix face_snapshot config[1/2] | ctl.c 30/0 |
| 16.0 | `2d0a17e388210e52eb936889836840532ff59f69` | [CAP]face_report:fix segment fault when load from flash failed | stat.c 3/3 |
| 17.0 | `2900128f10da10f075a1953a1ed814834f38dec9` | [all] avts: fixed the issue where the iot message of hub_storage proxy lacked faceid, name, and alias fields, resulting in the failure of pushing iot for face events [1/2]  avts : 修复hub_storage代理的iot消息缺少faceid、name、alias字段导致人脸事件推送iot失败的问题[1/2] | ctl.c 12/22 |
| 18.0 | `0fac6a5d2bc057c06c4eb7720cb4e972fedfab1f` | [all]cap:fix compilation error | ctl.c 8/2 |
| 19.0 | `6f4f42d77fdf07a6c131bc5f864da85f3cc71a82` | [all] fss: Optimize the validation process for the face_info file and fix a bug | ctl.c 1/1, stg.c 49/47 |
| 20.0 | `2fc6094a00eb449dda03c2050e34030192d2a5e7` | [all] fss: Optimize the validation process for the face_info file and fix a bug | ctl.c 1/1, stg.c 49/47 |
| 21.0 | `7bbf5e9a4a9f18aebe036de8832339ed2533def2` | [cap]fss:fix compile error and standardize code | ctl.c 4/0 |
| 22.0 | `c9e47da4b349dd4229c6be6dc627063ec33a049f` | [cap]face_snapshot:correct the storage path of fss | stg.h 1/1 |
| 23.0 | `593c131a451d7c6964221854396ff59b704658b5` | [CAP] merge (non-core)commit (interface capability variable) from nvmp_release_1.8.1_secure_enhance_250707 to other branch (3/5) | ctl.c 40/8, stat.c 5/1, fss.c 20/0 |
| 24.0 | `d86eea00d832658f90e55bb82ed00653dc9f0015` | [all]face_snapshot\|usr_cfg_conv:resolve the DOS attack caused by the connect interface(3/4) | ctl.c 1/0, stat.c 1/1 |
| 25.0 | `f76e5b845823c16e4fde0f0b7baefc629830ebbe` | [all] fss: fixed - face latest time update anomaly. | ctl.c 1/1 |
| 26.0 | `1ab529891045131033eef8f7e2b625932f15d02e` | [ALL] telemetry:telemetry support face recognition(2/3) | ctl.c 172/0, ctl.h 10/0 |
| 27.0 | `ebb0da210c6c5270f059715b454b2b64328ce82c` | [ALL] face_snapshot: Fix non-standard code for telemetry support of face recognition | ctl.c 8/6, ctl.h 1/1 |
| 28.0 | `dd2600fb397771d69ddfb4d7b41484f6e6f07ca9` | [Models with CAMERA_OPERATION_LOG_SUPPORT] cap:Add camera log (3/4) | fss.c 38/0 |
| 29.0 | `14378dec6d5e43e7deec71e79d9d732a71f1bdbb` | [Models with CAMERA_OPERATION_LOG_SUPPORT] cap: modify pre_set method(2/2) | fss.c 17/8 |
| 30.0 | `178f33f6da6a70893faecea14b1b51ef64bc62ac` | [all]cap:Fixed the error in determining the fd in err_exit | pss/recog_img_storage.c 2/2 |

## BC 物理独有焦点提交（65）

| 编号 | CAP 完整 SHA | 提交标题 | 路径内文件与行数 (+/-) |
| --- | --- | --- | --- |
| 1.0 | `54f4acfb6671f2fb3aeaaff4128cee45e04647a0` | [all] cap\|face_snapshot: support face_snapshot data model | Makefile 18/0, cfg/arming_schedule 11/0, cfg/feature_code 6/0, cfg/fss_gen_cfg 14/0, cfg/fss_pic_cfg 8/0, cfg/fss_rule 9/0, cfg/fss_size_cfg 9/0, cfg/region_info 13/0, cfg/size_limit 9/0, cfg/storage_head_info 13/0, fss.c 274/0 |
| 2.0 | `3c54793dd2751b0d1858bfa3c7839b4af2281c7a` | [all]change manufacturer name in NVMP platform code[4/5] | fss.c 1/1 |
| 3.0 | `450a0bbeeca02def4872e72949adcb95d33fa3b6` | [all]cap:add face detect base function(2/2) | Makefile 6/0, ctl.c 3305/0, ctl.h 199/0, fea.c 693/0, fea.h 151/0, stg.c 1285/0, stg.h 234/0, stat.c 1398/0, stat.h 150/0, stat_stg.c 1417/0, stat_stg.h 273/0, ver/ver.c 58/0, ver/ver.h 31/0, cfg/feature_code 1/1, cfg/storage_head_info 4/3, fss.c 143/33, ring_object.c 125/0, ring_object.h 69/0 |
| 4.0 | `3d14c077baee267afc2ee45a4a52ac0720bc888b` | [all]cap:read ams config for fss threshold set(1/2) | ctl.c 17/7, fea.c 135/3, fea.h 27/4, fss.c 118/0 |
| 5.0 | `7a5ee0dfba0152e57e4f89dc6865a2ad1a608bde` | [all] fss\|face_snapshot: Add support for finding best match function interface(2/2) | ctl.c 35/7, stg.h 0/1 |
| 6.0 | `26843acc363708ee4975ef04a9b87b23215a60ec` | [all]cap:save face data before AOV | stat.c 8/1 |
| 7.0 | `b49a124e00f5f79db64923bb3ad6d164068b0879` | [all] face_snapshot: prioritize adding familiar face,when the same person is in both group | ctl.c 10/0 |
| 8.0 | `bceb7fbc8a32b40d7ec29ed88f9f61560b181f1c` | [all] face_snapshot: keep msgpush when unfamilar people change to familar | ctl.c 12/0 |
| 9.0 | `9688a83c6e01899ce0b8213ca3bc0d5eab26872b` | [All] fss: Fix incorrect close file descriptor 0 and file descriptor leaks | stg.c 4/10 |
| 10.0 | `fcda83d10c63d9ee7a64d7fd6f487eb692d146e7` | [all] face_snapshot: IoT Wi-Fi Monthly/Weekly FD Statistics (2/4) | ctl.c 9/0, stat.c 249/3, stat.h 15/0, stat_stg.c 14/0, stat_stg.h 9/1 |
| 11.0 | `7b54cd2e9f4f1ecdbe467d8d57df7294d98b4c12` | [all] face_snapshot: Fix compilation warnings | stat.c 6/5 |
| 12.0 | `e61493059dff8202b1d4f8ecd2523aa0b21079a4` | [ALL] fix compilation error | stat.c 2/0 |
| 13.0 | `22c12edfc09bcceee973ccdfafc30a90436f57cb` | [All] cap/fss: remove unnecessary logs | fss.c 0/1 |
| 14.0 | `285018e33f5d633df02e7d24621432b0e78b0af4` | [all]face snapshot: fix face utc time incorrect problem | ctl.c 17/1 |
| 15.0 | `d161ecab8a886dde5f153763e0fb4874c56be083` | [all]face_snapshot\|hub:add hub support and skip tapocare msgpush when face is detected(2/2) | ctl.c 49/20 |
| 16.0 | `96438c16882e200327e93e317dc4d4451ba36667` | [all] face_snapshot: Fix Incorrect Face Result Timestamp | ctl.c 1/1 |
| 17.0 | `645eb8f0acaafdb55b06f81b0c0801191432b3db` | [all]face snapshot:face detect msg push when upto push threshold(1/2) | ctl.c 66/71, ctl.h 7/0, stat.c 1/0, fss.c 24/0 |
| 18.0 | `cd9bc9160cd18b212a5c5de17b5255db8aa58381` | [All] cap/fss: use callback to attach ringbuffer instead of timer retry (2/2) | ctl.c 32/40 |
| 19.0 | `99edff3d1aea0e4eb6724d5ddffb63dd6d2820ae` | [cap]face_snapshot:fix some bugs of face snapshot | ctl.c 135/43, stat.c 5/2, stat.h 2/1 |
| 20.0 | `71c4e67b2a7634e48d7d312a93bc0289ba580d3b` | [cap]face_snapshot:fix the issue introduced by the submission of 1cfaf2 | ctl.c 33/24 |
| 21.0 | `3178a777405af52717e7f932d23e183856c9a4e3` | [all] face_snapshot: fix a bug that face msg push failed when face name contains specified character. | ctl.c 49/2 |
| 22.0 | `95abd9522ccadcc3f6250f159213a2bd73e74ad5` | [all]face_snapshot: save face index when the face keeps appearing in front of the camera before power down(2/2) | ctl.c 1/1 |
| 23.0 | `41903f2d380f07ad02842bf6ba53bbe7ac862739` | [CAP]face_report:fix segment fault when load from flash failed | stat.c 3/3 |
| 24.0 | `ea1f1e58e27219d43e466ec8c5c06d2e9006d6bc` | [all] fss \| face_feature: add fss adapt iqa_thresh (2/2) | fea.c 16/1, fea.h 8/3, fss.c 12/0 |
| 25.0 | `0bb947224bc08bdfc400aaa353d437f29e573e64` | [FSS] Recalculate face features when face recognition model is updated (2/3) | ctl.c 167/0, fss.c 20/0 |
| 26.0 | `bad5f512f868b751170c565d1abd90bf5cde1b62` | [all] cap\|face_snapshot: feature matching func is valid for familar | ctl.c 9/0 |
| 27.0 | `e20c27274731bf2c7f749083439a8c824bab8844` | [all] fss: fixed that the face nums diff before and after the merge. | stat_stg.c 1/1 |
| 28.0 | `8afda7b47cc26866765f0cd081f65a428a1a6da3` | [FSS] Add filter conditions for size score(2/2) | fea.c 6/2, fea.h 2/0, fss.c 6/0 |
| 29.0 | `0cc155658dbd4c2850d31fdefb4420404c96ee0f` | [all]face_snapshot:fix dead lock and timeout time | stat.c 11/2, stat.h 6/0, stat_stg.h 6/0 |
| 30.0 | `98a8b58b1ca286996107fed5050f446f01f55a98` | [all] fss: Optimize the validation process for the face_info file and fix a bug | ctl.c 1/1, stg.c 49/47 |
| 31.0 | `63f6159460300afafb0a3feac3279c116d855daf` | [ALL] Add a synchronization access mechanism for active face info and inactive face info files | stg.c 23/0 |
| 32.0 | `49cc1cd51e7fd157c88b98815d271040cd70b45b` | [ALL] Reduce the unnecessary operations of writing the face info file | stg.c 15/9, stg.h 4/2 |
| 33.0 | `9aec74acb24a15a79d0bc0f67bb7aca395d78c0e` | [ALL] SAST: Fix sprintf, add field width specifier to fscanf(), and check rturn value of chdir() | stat_stg.c 16/2 |
| 34.0 | `1403e6830e471144cf71112c23175731edee6025` | [all] cap/fss: support pss (2/2) | Makefile 5/0, ctl.c 631/48, ctl.h 9/0, fea.c 67/3, fea.h 17/4, stg.h 10/0, pss/pdr_storage.c 210/0, pss/pdr_storage.h 112/0, pss/recog_img_stg_version.c 97/0, pss/recog_img_stg_version.h 47/0, pss/recog_img_storage.c 1233/0, pss/recog_img_storage.h 142/0 |
| 35.0 | `caab424ca6830e1250f42ebf36686eba8c9ef0fd` | [All] cap/pss: reduce max person_num and max person snapshot size | pss/pdr_storage.h 3/3 |
| 36.0 | `6b0eefe8e1f3510c79d0800fb481cf90bb15c7aa` | [all] cap: Error on loading the human figure data after device restart, which led to the need to rebind the human figure to new data and affected the consistency of the facial data | fea.c 1/1 |
| 37.0 | `0bb585cbc73137e4e67680d37092d93f5055b182` | [all] cap: The failure to update the feature values of the face image through the algorithm interface leads to the generation of incorrect feature values in database, inducing high-frequency false recognization | ctl.c 20/6 |
| 38.0 | `1a03e63298ff39ec1b1890dce4999fea31322b10` | [all] face_control: Support doFaceInfoAddPacketized API (1/2) | ctl.c 470/92, fss.c 1/0 |
| 39.0 | `be139db67a4bad56399516ccefd4c83018810add` | [ALL] cap: delete redundant code | stg.c 13/15 |
| 40.0 | `d8eb1b19e29eacd3950dcfa550aba9564863593a` | [ALL] Correct the logical errors in the function fd_control_udsd_usr_add_face | ctl.c 5/4 |
| 41.0 | `7e7c0f156c2970259929cf60784af3631dcdc0b9` | [ALL]cap: delete redundant code | ctl.c 0/7 |
| 42.0 | `08fd905b3a589373d76af5d46a5fd854a316d7c3` | [all] fss: fixed face data lost (1/2) | stg.c 77/2 |
| 43.0 | `ea33fe4d4a27504ed9284dc8bd5daead504c6bca` | [CAP] Security Optimization for DS Interface (3/4) | ctl.c 45/10, stat.c 6/1, fss.c 20/0 |
| 44.0 | `bb3848b5598b600095f3665859111b6d59f7b9b6` | [ALL] face_snapshot: add scene-aware real-time feature update for familiar faces | ctl.c 183/1, fea.c 33/1, fea.h 14/1, stg.c 15/2, stg.h 3/1 |
| 45.0 | `ca53b60a4cc53ac4902401092709428702a3f668` | [all]cap:resolve the DOS attack caused by the connect interface(3/4) | ctl.c 1/0, stat.c 1/1 |
| 46.0 | `439b9c8b9bb4205e027a5d6fdeed5a44f0bd392c` | [all] fss: fixed - face latest time update anomaly. | ctl.c 1/1 |
| 47.0 | `7012ac55e8970c87146e8e5f740454d2c4d84350` | [all]cap: support enhanced package detection [2/5] | ctl.c 22/0 |
| 48.0 | `ce7ab9a6169954d89f0a86379e75321c1baa2fa6` | [ALL]nvmp\|cap: Wrap localtime_r/gmtime_r, unify time conversion APIs across NVMP platform[3/4] | stat.c 20/14 |
| 49.0 | `e933738e1f6b75a20eb2323aa0796c04fa1194f0` | [cap] fd_statistics: fix null pointer memset compile error in monthly mode | stat.c 1/1 |
| 50.0 | `6bf25ceb87ec8e0967db1f54f6802149f3e38d79` | [cap] en_pkgd\|face_snapshot: update package history when face detected (1/2) | ctl.c 34/6 |
| 51.0 | `b8e8a80294fc5f063c82dffb2f4d4620f4e5baeb` | [cap] en_pkgd: add macro control for local package history maintainance logic | ctl.c 2/2 |
| 52.0 | `3ec3c0ef990abb98e4b4afa30070c6f5fe7cda9e` | [ALL] CAP\|cap: Fix NAND firmware packaging and add battery cam branch compatibility [3/5] | ctl.c 23/1, stat.c 2/0 |
| 53.0 | `a8aed44ebc4b24f0cc45584ad64f1eba52edac21` | [ALL] CAP\|log : adapt module-based logging and unify msg_debug interface[3/4] | stg.h 3/3 |
| 54.0 | `80f2e265321dd11e085d7b8dfdeec64d70c351a8` | [all] face_snapshot: malloc correct image size for face image | ctl.c 1/1, fea.c 16/1 |
| 55.0 | `1186c1861d4eadc7a933b85c688130213c933d16` | [All] cap/fss: fix crash during app get snapshot that size larger than max_img_len | ctl.c 15/3 |
| 56.0 | `03c33af88e5fdf6302bebcce676e9a0081ed3d2f` | Revert "Merge "[ALL] CAP\|log : adapt module-based logging and unify msg_debug interface[3/4]" into develop/bc_develop_220927" | stg.h 3/3 |
| 57.0 | `8f72dafca02825230827e9c2f212a3fd833bbb45` | [ALL] CAP\|log : adapt module-based logging and unify msg_debug interface[3/4] | stg.h 7/1 |
| 58.0 | `b9ede40350c03b0fb404b0a6505722232ffd2c0b` | [fss] face_control: Save unselected familiar face detection notify list | ctl.c 1/0 |
| 59.0 | `48e74a2785dc75597636ea35f1e8e7d180036d5c` | [all] face_control: include HUB fields for familiar and unfamiliar recongition events | ctl.c 12/2 |
| 60.0 | `be46f65124e1a38b0538e0a1096c8846e80feff3` | [cap] face_snapshot: merge AC logic in BC (feature/storage basis) | ctl.h 16/1, fea.c 185/3, fea.h 61/0, stg.c 185/0, stg.h 28/2, stat.h 19/0, stat_stg.h 69/1, ver/ver.c 130/0, fss.c 77/0, pss/pdr_storage.h 16/1 |
| 61.0 | `f96c42168ed1262f07bb1afb6240645ad4e24ff6` | [cap] face_snapshot: merge AC logic in BC (fd_statistics family + pss storage + default config) | Makefile 6/0, stat.c 175/25, stat_stg.c 133/14, cfg_ac/storage_head_info 14/0, pss/recog_img_storage.c 326/0 |
| 62.0 | `bb3085b88fbccd3b515d2ee7859417e807b7180f` | [cap] face_snapshot: merge AC logic in BC (face_control) | ctl.c 1194/48 |
| 63.0 | `13f832c751368d15618ae7d9209634f6657d7429` | [CAP] face_control: fix compile error | ctl.c 2/0 |
| 64.0 | `1c851e9523057d6166204f99e78859a994527e2b` | ﻿[cap] face_snapshot: clean redundant macro guards and optimize function layout in face_control | ctl.c 65/125 |
| 65.0 | `3e40aa2606ea54ff93f9b39deeddb7cd970d351b` | [all] face_control: add qualified face tags for pss recognition | ctl.c 49/13 |
