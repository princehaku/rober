# Final：O1 verified upload / backup / vendor additive instrumentation

## 收口结论

- `PRODUCT_CLOSEOUT=ACCEPT_CURRENT_SUPPORTING_MAINTENANCE_DELTA_BLOCKED_FAIL_CLOSED_FLAT_ROUTE_NONE`
- `status=closed_current_strict_no_motion_attempt_consumed_blocker_exhausted_2_of_2`
- `artifact_status=verified_upload_backup_vendor_instrumentation_blocked_fail_closed`
- `proof_boundary=current_verified_upload_backup_vendor_instrumentation_maintenance_evidence_not_hil`
- `first_failure=verified_esptool_version_unavailable`
- Gate U / Gate B / Gate V-prebuild=`false/false/false`
- O1=`~95%` flat；KR `不归档`；历史区无新增。

本 Epic 完成 runner、19 个 targeted tests、canonical vendor V0.9 additive patch/toolchain 合同、硬件文档与唯一 current
strict-no-motion live attempt。Product 接受 current port/toolchain NO-GO、正确跳过 backup/build/flash 和完整恢复证据；
不接受 instrumentation、current flash backup、HIL、安全准入、route、delivery 或 mission credit。

## 用户价值、产品北极星与核心抓手

用户价值是防止在目标 ESP32 upload identity 未证明、current firmware 无可恢复副本、toolchain 不可复现时盲刷。产品北极星
是可信、安全、可解释的真实底盘控制与反馈闭环。

本轮核心抓手是 current Gate U/B/V 串行 fail-closed，而不是 inventory wrapper：唯一 SSH attempt 真实区分了 STC
`ttyACM0` 与 normal UART `/dev/ttyS5`，并在 pinned toolchain 不存在时停止所有下游 mutation。

## 实际交付与 Engineer 验证

Hardware 实际交付：

- `o1_verified_upload_backup_vendor_instrumentation.py` 与 19 个 targeted tests；
- isolated vendor V0.9 diagnostic `platformio.ini`、additive patch 与 `toolchain.lock`；
- fixture/mock artifact 与唯一 current live artifact；
- 更新后的 `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md`；
- `tech-done.md` 的完整 ledger、首轮失败、post-live 本地加固和剩余风险。

Engineer 留档验证为 py_compile exit `0`、`Ran 19 tests in 0.108s / OK`、fixture/JSON/schema/assertions/scoped diff 全绿，
中文技术注释比例 runner/tests=`20.20%/20.61%`。Product 只读核对既有 evidence，没有重跑任何工程测试或 live 命令。

## Current artifact、Gate 与 exactly-once 事实

主 artifact schema=`trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1`，status=
`verified_upload_backup_vendor_instrumentation_blocked_fail_closed`，`artifact_validation_errors=[]`。

- runner/attempt/inventory/pre-stop/service-stop/service-restore/final-stop=`1/1/1/1/1/1/1`；
- SSH transport invocation=`1`、exit=`0`；
- Gate U=`false`：唯一 stable alias 是 STC USB Serial -> `ttyACM0`，pinned esptool `4.8.1` 不可用，
  bootloader probe=`0`，`normal_uart_is_upload_identity=false`；
- Gate B=`false`：current flash backup read=`0`，factory target 没有替代 current backup；
- Gate V-prebuild=`false`：canonical 26-file source manifest/hash 匹配且 generic `main.cpp` absent，但 live patch 对 CRLF
  产生 `.orig/.rej`，PlatformIO `6.1.18` 与 esptool `4.8.1` 不可用；
- build/diagnostic-flash/stationary-readback/rollback/motion/T900/retry=`0/0/0/0/0/0/0`；
- service/holder/final stop=`true/true/true`，五个 deployed hashes unchanged，run-owned residual=`false`。

live 后 CRLF normalization 只在本地加固并通过离线复验，没有第二次 SSH/live；不得倒推 Gate V current green。

## OKR 映射、方向判断与 KR 历史

- O1 约 `95%`：方向从“继续当前 hardware lane”调整为
  `暂停本 lane，等待物理 upload port/toolchain 外部条件变化`。
- O5 约 `85%` production provider/runtime lane 已 `2/2`；O6/O7 各约 `93%` corrected Phase0 lane已 `2/2`；
  O1 本 hardware lane 本轮也达到 `2/2`。当前没有 admissible Objective。
- `current_run_artifact_delta=1` 与 `external_artifact_delta=1` 只表示 current real-board maintenance supporting evidence；
  `live_control_delta=0`、`okr_credit=false`。
- `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、
  `mission_attempt=false`、`mission_objective_0_satisfied=false`。
- O1 KR 全部 `不归档`；当前推进区不移动，已完成 KR 历史区无新增。证据位置是本 sprint `tech-done.md`、live artifact、
  `side2side_check.md` 与本 `final.md`。

## Blocker 2/2、route 与下一轮

canonical blocker
`verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing` 已从前序 `1/2` 达到 `2/2`。
下一轮禁止第三次 port inventory、bootloader readiness、backup plan、vendor patch/toolchain summary、CRLF-hardening-only 或等价
wrapper，也不得原地重跑本 attempt。

`ROUTE=NONE_REQUIRES_PHYSICAL_ESP32_UPLOAD_PORT_CONNECTION_AND_PINNED_TOOLCHAIN_OR_NEW_EXTERNAL_EVIDENCE`

`SPRINT=SKIPPED_NO_ADMISSIBLE_LANE`

CEO/现场最小解锁动作：

1. 按 vendor wiki 将驱动板中间 USB 连接到上位机或维护主机，使 WAVE ROVER ESP32 bootloader port 真实出现；
2. 在维护主机预装并 pin `esptool 4.8.1` 与 `PlatformIO 6.1.18`；
3. 保持 operator 在场、路线清空与物理限位。

这不是重新授权请求：完整 service/UART/firmware maintenance authorization 已存在。若 O1 条件不变化，也可由新的 O5
success-class production evidence，或 O6/O7 新的 route/delivery/operator/current external evidence 解锁不同 lane；在外部状态
变化前不新建 sprint。

## 风险、缺失证据与完成前反思

剩余风险：

1. current WAVE ROVER ESP32 bootloader/upload port、chip/flash identity 未证明；
2. current full-flash backup、rollback image、diagnostic build/image provenance 未建立；
3. firmware identity、runtime `mainType/moduleType`、raw encoder A/B counters 仍不可观测；
4. current nonzero wheel feedback、HIL、safe-to-control、route execution、delivery/operator acceptance 和 mission 均未证明；
5. post-live CRLF portability 加固只有离线证据，不是 current-board proof。

Epic 六文档已完成；Hardware 相关 docs 已同步。本 Product 收口只新增/修改允许的四个文档，不改 Engineer
implementation、tests、artifacts、planning docs 或 `tech-done.md`，不 commit/push。
