# Side-to-side Check：O1 verified upload / backup / vendor additive instrumentation

## 对照结论

- `SIDE2SIDE=ACCEPT_CURRENT_SUPPORTING_MAINTENANCE_DELTA_BLOCKED_FAIL_CLOSED_FLAT`
- `PRODUCT_CLOSEOUT=ACCEPT_CURRENT_SUPPORTING_MAINTENANCE_DELTA_BLOCKED_FAIL_CLOSED_FLAT_ROUTE_NONE`
- `artifact_status=verified_upload_backup_vendor_instrumentation_blocked_fail_closed`
- `proof_boundary=current_verified_upload_backup_vendor_instrumentation_maintenance_evidence_not_hil`
- `first_failure=verified_esptool_version_unavailable`
- Gate U / Gate B / Gate V-prebuild=`false/false/false`
- O1 保持约 `95%`；KR `不归档`；历史区无新增。
- canonical blocker
  `verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing=2/2`

用户价值是避免把 normal UART、无 current backup 的 firmware 或不可复现 toolchain 当成可安全刷写链路。产品北极星仍是
可信、安全、可解释的真实底盘控制与反馈闭环。Product 接受本轮 current strict-no-motion upload/backup/toolchain
fail-closed 与完整恢复 supporting delta；拒绝 instrumentation、HIL、safe-to-control、route、delivery 或 mission credit。

## PRD / Tech Plan 与最终事实对照

| 验收项 | 计划口径 | 最终事实 | 判定 |
| --- | --- | --- | --- |
| 唯一 attempt | runner/attempt/SSH 各一次，无 retry | runner/attempt/SSH=`1/1/1`，SSH exit=`0`，retry=`0` | PASS |
| Gate U | stable alias + current bootloader identity + pinned esptool | 唯一 alias 是 `usb-STC_STC_USB_Serial-if00 -> ttyACM0`；pinned esptool `4.8.1` 不可用，bootloader probe=`0`；`/dev/ttyS5` 明确不是 upload identity | BLOCKED / fail closed |
| Gate B | Gate U 绿后读取一次 current full flash backup | Gate U 红；flash backup read=`0`，factory target 未冒充 current backup | PASS / correctly skipped |
| Gate V-prebuild | canonical vendor V0.9 source、additive patch、pinned toolchain 全绿 | 26-file canonical manifest 与 required hashes 匹配，generic `main.cpp` 未混入；但 live patch 对 CRLF 生成 `.orig/.rej`，PlatformIO `6.1.18` / esptool `4.8.1` 不可用 | BLOCKED / fail closed |
| Build/flash/readback/rollback | U/B/V-prebuild 全绿后各最多一次 | `0/0/0/0` | PASS / correctly skipped |
| 禁止 motion/T900 | 全程严格为 0 | motion/T900=`0/0`，也没有 manual、`/cmd_vel` 或 Nav2 | PASS |
| 恢复 | service/holder/hash/final stop/residual clean | service/holder/final stop=`true/true/true`，五个 deployed hashes unchanged，residual=`false` | PASS |
| 离线质量 | py_compile、19 tests、fixture/JSON/assertions、中文注释 >20%、scoped diff | Engineer 留档全部通过；注释 runner/tests=`20.20%/20.61%` | PASS / Engineer evidence accepted |
| post-live 加固边界 | 本地修复不能倒推 current live | CRLF normalization 仅本地加固并离线复验；没有第二次 SSH/live | PASS / current Gate V 仍 false |

## Current artifact 只读核对

Product 只读接受以下 artifact 事实：

- schema=`trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1`；
- status=`verified_upload_backup_vendor_instrumentation_blocked_fail_closed`；
- `artifact_validation_errors=[]`、errors=`[]`；
- inventory/pre-stop/service-stop/service-restore/final-stop=`1/1/1/1/1`；
- bootloader-probe/backup/build/diagnostic-flash/readback/rollback/motion/T900/retry=`0/0/0/0/0/0/0/0/0`；
- service 从 active/running PID `6422` 恢复为 active/running PID `7516`；
- expected holder 从 PID `6872` 恢复为 PID `7966`，command hash prefix 相同；
- `service_restored=true`、`holder_restored=true`、`final_stopped=true`、`run_owned_residual=false`；
- `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、
  `mission_attempt=false`、`okr_credit=false`。

Product 没有重跑 tests、SSH、service、UART、firmware、build、flash、rollback、T900 或 motion。

## OKR、KR、blocker 与方向

- O1 方向=`暂停当前 upload/backup/toolchain lane，等待外部物理条件变化`；约 `95%` flat。
- O5 约 `85%`，production provider/runtime lane 已 `2/2`；O6/O7 各约 `93%`，corrected Phase0 lane 已 `2/2`。
- O1 当前 canonical blocker 本轮达到 `2/2`，禁止第三轮 upload inventory、readiness、source-hardening、backup plan、
  toolchain summary 或等价 wrapper。
- 所有 KR `不归档`；当前推进区不移动，历史区无新增完成项。
- 完整 maintenance authorization 仍有效；当前缺口不是重新授权。

当前没有 admissible lane：

`ROUTE=NONE_REQUIRES_PHYSICAL_ESP32_UPLOAD_PORT_CONNECTION_AND_PINNED_TOOLCHAIN_OR_NEW_EXTERNAL_EVIDENCE`

`SPRINT=SKIPPED_NO_ADMISSIBLE_LANE`

## 下一轮与最小解锁动作

下一轮不得新建第三个同 blocker sprint。CEO/现场最小解锁动作是：

1. 按 vendor wiki 拆机并把驱动板中间 USB 接口连接到上位机或维护主机，使目标 ESP32 bootloader port 真实出现；
2. 在维护主机预装并 pin `esptool 4.8.1` 与 `PlatformIO 6.1.18`；
3. 保留 operator 在场、路线清空和物理限位；不需要重新授予既有完整维护授权。

只有上述物理连接/toolchain 条件出现，或 O5/O6/O7 获得新的 success-class production、route、delivery/operator 等外部证据，
才重新路由。条件未变化时保持 route-none，不制造新 sprint。
