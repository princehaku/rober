# Side-to-side Check：O1 runtime identity / raw encoder 独占维护

## 对照结论

- `SIDE2SIDE=ACCEPT_CURRENT_SUPPORTING_MAINTENANCE_DELTA_BLOCKED_FAIL_CLOSED_FLAT`
- `sprint_path=sprints/2026.07.28_17-59_o1_runtime_identity_raw_encoder_maintenance/`
- `artifact_status=maintenance_blocked_fail_closed`
- artifact `evidence_boundary=current_exclusive_maintenance_fail_closed_not_hil`
- Product `proof_boundary=current_exclusive_maintenance_runtime_feedback_toolchain_and_restoration_evidence_not_hil`
- O1 保持约 `95%`；KR `不归档`；历史区无新增。

用户价值与产品北极星仍是可信、安全、可解释的真实底盘控制与反馈闭环。本轮不是又一份维护计划：旧
`paused_pending_exclusive_maintenance_authority` 已被 CEO 完整维护授权解除，并由唯一 current live runner 真实消费。Product
接受 current service/UART/runtime-feedback/toolchain/restoration supporting delta；但 runtime identity、raw counter、
instrumentation/HIL/route/delivery/mission 均未闭合，因此不计主 OKR 百分比。

## PRD / Tech Plan 与最终事实对照

| 验收项 | 计划口径 | 最终事实 | 判定 |
| --- | --- | --- | --- |
| 唯一维护窗口 | runner/window/inventory 各一次，禁止 retry | runner/window/inventory=`1/1/1`，SSH transport invocation=`1`、exit=`0`，retry/second motion=`0/0` | PASS |
| 独占 service/UART | pre-stop、service stop、holder empty 后独占一次 `/dev/ttyS5@115200` | pre-stop/service-stop/UART-open=`1/1/1`；holder termination=`0`；pyserial `3.5` 可用 | PASS |
| current feedback | 读取 current `T=1001` 与 runtime/raw counter 字段 | 收到 `57` 帧 `T=1001`，全部 `L/R=0/0`，keys 仅 `T/L/R/r/p/y/v`；firmware identity、runtime `mainType/moduleType` 均 `null`，raw A/B samples=`0/0` | BLOCKED / useful current evidence |
| instrumentation gate | upload port、backup、toolchain/provenance 全绿才 build/flash | verified upload port、PlatformIO/esptool、current flash backup provenance 未观测；build/flash/rollback=`0/0/0`，未创建或刷入 generic binary-protocol image | FAIL-CLOSED |
| motion gate | observability 全绿后最多一次 nonzero | `counter_feedback_observability_gate=false`，nonzero/post-motion-stop=`0/0`，没有消费 motion | PASS / correctly skipped |
| 恢复与 final stop | service/holder/hash/stop 全部恢复 | service active/running；bounded read-only post-restore 证明 expected bridge child PID `6872` 重占 `/dev/ttyS5`；`holder_restored=true`、deployed hashes unchanged、`final_stopped=true` | PASS |
| 安全边界 | instrumentation 不冒充 HIL/mission | `instrumentation_success=false`、`hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`mission_attempt=false` | PASS |
| 离线质量 | 17 tests、fixture、JSON、assertions、validator、diff、中文注释严格通过 | `tech-done.md` 记录 py_compile exit `0`、`Ran 17 tests ... OK`、fixture/JSON/artifact assertions/post-restore/live validator/scoped diff 通过，注释 `20.18%/20.51%` | PASS / Engineer evidence accepted |

## Artifact 与恢复核对

Product 只读核对：

- `artifacts/maintenance_result.json` schema=`trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1`、
  status=`maintenance_blocked_fail_closed`，validation errors 与 errors 均为空。
- counts：
  `runner/window/inventory/pre-stop/service-stop/UART-open/T900/final-stop/service-restore=1/1/1/1/1/1/1/1/1`；
  build/flash/rollback/nonzero/post-stop/retry/second-motion=`0/0/0/0/0/0/0`。
- current runtime/raw facts：57 帧 T1001 全部 `0/0`；firmware identity、runtime main/module type、raw counter delta 均
  `null`，raw A/B samples=`0/0`。
- `artifacts/post_restore_verification.json` schema=`trashbot.wave_rover.post_restore_verification.v1`、
  `read_only=true`、`expected_holder_observed=true`；service/firmware/UART-open/UART-write/motion mutation 全部为 `0`。
- service before/after 均为 active/running；最终 expected bridge holder 已恢复，部署 hashes 前后一致，rollback 为
  `no_flash_performed` 的显式 no-op，`run_owned_residual=false`。

Product 没有重跑 Hardware tests、live runner、SSH、service、UART、firmware 或 motion。

## OKR、KR、方向与 blocker 语义

- 方向判断：O1 `继续`，但从“等待独占维护授权”调整为“维护授权已真实消费，转入 firmware diagnostic toolchain
  prerequisites”；不回到旧授权 blocker，也不回到 O5/O6/O7 已消费 `2/2` 的 wrapper families。
- Product 接受 `current_run_artifact_delta=1` 与 `external_artifact_delta=1`，仅表示 current live maintenance supporting
  evidence；`live_control_delta=0`、`user_action_delta=0`、`okr_credit=false`。
- O1 保持约 `95%`，因为没有 current runtime identity/raw counter observability、nonzero wheel feedback、HIL、
  safe-to-control、route execution、delivery/operator acceptance 或 mission attempt。KR `不归档`，历史区无新增。
- 新 canonical blocker：
  `verified_esp32_upload_port_flash_backup_vendor_v0_9_diagnostic_toolchain_provenance_missing`，首次消费 `1/2`。它不同于已解除的
  maintenance-authority blocker，也不同于已退役的 v8 motion/readback slice。

## 下一条可执行 lane 与验收口径

P0 owner=`rober-hardware-engineer`。另立新 attempt 的 strict no-motion instrumentation-prerequisite lane，只允许先建立：

1. verified ESP32 upload alias/port identity；
2. 可复核的 current flash backup、hash 与 rollback provenance；
3. canonical vendor V0.9 additive diagnostic build/toolchain provenance。

同一 attempt 禁止重跑本 maintenance runner、`T=900` 或 motion；不得 build/flash，直到 upload/backup/provenance gate 全绿。下一
lane 的最小验收是 machine-readable upload identity + current backup hash + vendor source/patch/build provenance，并持续固定
HIL/safe/route/delivery/mission 为 false。
