# Final：O1 runtime identity / raw encoder 独占维护

## 收口结论

- `PRODUCT_CLOSEOUT=ACCEPT_CURRENT_SUPPORTING_MAINTENANCE_DELTA_BLOCKED_FAIL_CLOSED_FLAT`
- `status=closed_current_maintenance_consumed_new_toolchain_blocker_1_of_2`
- `artifact_status=maintenance_blocked_fail_closed`
- `proof_boundary=current_exclusive_maintenance_runtime_feedback_toolchain_and_restoration_evidence_not_hil`
- O1=`~95%` flat；KR `不归档`；历史区无新增。

本 Epic 完成代码、测试、硬件文档、唯一 current live maintenance 与恢复闭环。旧独占维护授权 blocker 已解除并被真实消费；
本轮把“不知道 ESP32 当前 runtime/raw counter”推进为 current direct UART 和 toolchain fail-closed 事实，但没有拿到 firmware
identity、runtime `mainType/moduleType` 或 raw encoder counters。Product 接受 supporting maintenance delta，不接受
instrumentation、HIL、安全准入、路线、送达或 Mission credit。

## 用户价值、北极星与本轮核心抓手

用户价值是避免在底盘反馈仍不可解释时重复运动或盲刷 firmware。北极星是可信、安全、可解释的真实底盘控制与反馈闭环。
本轮核心抓手是消费已授权的独占 service/UART 维护窗口，直接观察 current T1001、runtime/raw-counter 字段、现场
instrumentation toolchain 和完整恢复状态；不是 review、handoff 或 status wrapper。

## 实际交付与 Engineer 验证

Hardware 实际交付 runner、17 个 targeted tests、fixture/mock artifact、唯一 current maintenance artifact、post-restore
artifact 和更新后的硬件文档。`tech-done.md` 留档证据为：

- py_compile exit `0`；`Ran 17 tests in 0.086s / OK`；
- fixture status=`fixture_complete`，JSON parse 通过；
- maintenance / post-restore JSON、完整 artifact assertions 与 live validator errors=`[]` 通过；
- scoped `git diff --check` 通过；
- 中文技术注释比例 runner/tests=`20.18%/20.51%`。

Product 仅核对既有 evidence，没有重跑 Hardware tests、live runner、SSH、service、UART、firmware 或 motion。

## Current artifact、计数与硬件事实

主 artifact schema=`trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1`，status=
`maintenance_blocked_fail_closed`，artifact boundary=`current_exclusive_maintenance_fail_closed_not_hil`，validation
errors/errors 均为空。

- exactly once：
  runner/window/inventory/pre-stop/service-stop/UART-open/T900/final-stop/service-restore=`1/1/1/1/1/1/1/1/1`；
  SSH transport invocation=`1`、exit=`0`。
- no retry/motion/flash：
  build/flash/rollback/nonzero/post-stop/retry/second-motion=`0/0/0/0/0/0/0`。
- current UART：RX current `T=1001`=`57`，全部 `L/R=0/0`，字段只有 `T/L/R/r/p/y/v`；raw encoder A/B
  samples=`0/0`，counter delta=`null/null`。
- identity：firmware identity、runtime `mainType`、module type before/after 全部 `null`；`T=900` write=`1` 不能替代
  runtime readback。
- instrumentation：`instrumentation_required=true`、`instrumentation_success=false`；PlatformIO、Arduino CLI、esptool、
  verified upload port 与 current flash backup provenance 未观测，故 build/flash=`0/0`。
- restoration：service active/running；bounded read-only post-restore 确认 expected bridge child PID `6872` 重新持有
  `/dev/ttyS5`，`holder_restored=true`；deployed hashes unchanged、`final_stopped=true`、
  `run_owned_residual=false`。

## OKR 映射、方向判断与 KR 历史

- O1 方向=`继续但调整下一抓手`。O1 保持约 `95%`：本轮只有 current supporting maintenance evidence，没有 current
  runtime/raw-counter observability、nonzero feedback、HIL、安全准入、route、delivery/operator acceptance 或 mission。
- Product 接受 `current_run_artifact_delta=1` 与 `external_artifact_delta=1` 为 supporting current live maintenance delta；
  `live_control_delta=0`、`user_action_delta=0`、`okr_credit=false`。
- `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、
  `mission_attempt=false`、`mission_objective_0_satisfied=false`。
- O1 KR 全部 `不归档`；当前推进区不移动，已完成 KR 历史区无新增。证据位置为本 sprint `tech-done.md`、
  `side2side_check.md`、主/post-restore artifacts 和本 `final.md`。
- O5 provider/runtime 与 O6/O7 corrected Phase0 wrapper families 继续保持各自 `2/2` 退役边界；本轮不回到这些 lanes。

## Blocker count、风险与下一条 lane

已解除并真实消费的旧 blocker 是 exclusive service/UART/firmware maintenance authority；不得再写
`paused_pending_exclusive_maintenance_authority`。新的 canonical blocker 是
`verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing`，首次消费 `1/2`。

剩余风险：

1. deployed firmware identity、runtime `mainType/moduleType`、raw encoder A/B counters 与 counter delta 未观测；
2. 57 帧静止 T1001=`0/0` 不能推导 encoder 损坏，也不能推导 HIL pass/fail；
3. current upload port、flash backup、PlatformIO/esptool 与 vendor V0.9 diagnostic provenance 未建立；
4. 本 attempt 已封存，禁止 runner、T900、motion、build/flash 补采或 retry。

下一条可执行 lane 只由 `rober-hardware-engineer` 负责：另立新 attempt 的 strict no-motion
instrumentation-prerequisite sprint，先建立 verified ESP32 upload alias/port、current flash backup/hash/rollback provenance
和 canonical vendor V0.9 additive diagnostic toolchain/source/patch/build provenance。三门全绿前不得 build/flash；firmware/
runtime/raw counters 无运动可读前不得 supervised minimal motion。新 blocker 若第二轮仍未关闭达到 `2/2`，下一轮必须切换
Objective 或升级 CEO，不得第三轮包装。

## 完成前反思

- Epic 六文档已完整；Product 仅修改允许的 `side2side_check.md`、`final.md`、`OKR.md` 和
  `docs/process/okr_progress_log.md`。
- 没有把 live artifact、service/UART/T900、`instrumentation_required=true`、恢复成功或 build/flash=`0` 误写成 HIL、
  safe-to-control、route、delivery 或 mission 完成。
- 没有回滚 Hardware 的代码、测试、docs、artifacts 或 `tech-done.md`，没有 commit/push。
