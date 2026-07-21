# Side-to-side Check：O1 轮速反馈根因诊断

## 对照结论

`SIDE2SIDE=ACCEPT_SUPPORTING_DIAGNOSTIC_IMPLEMENTATION_READONLY_RUNTIME_INVENTORY_FLAT`

旧 `REJECT_IMPLEMENTATION_NOT_STARTED_ACCEPT_PLANNING_BOUNDARY_ONLY` 已被同一 sprint 后续 Hardware business-worker 的真实实现、
验证和只读 inventory **supersede**；`pre_start.md` 中的旧状态只保留历史调度事实，不再代表最终交付状态。

- `sprint_path=sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/`
- `proof_boundary=offline_vendor_v8_diagnostic_plus_single_remote_readonly_inventory_supporting_only`
- O1 约 `95%` flat；KR `不归档`。
- `runtime_main_type_not_observed`、`runtime_firmware_identity_not_observed`。
- `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`。

| 验收项 | 计划口径 | 最终事实 | 判定 |
| --- | --- | --- | --- |
| 可执行诊断模块 | 稳定、fail-closed root-cause schema | 已新增离线 CLI；两个诊断 artifact 均为 `trashbot.wave_rover.feedback_root_cause_diagnostic.v1`、`status=diagnostic_complete_fail_closed`、`input_valid=true` | PASS |
| 单元测试与 CLI | py_compile、unittest、CLI 全绿 | Hardware 留档 py_compile exit `0`、`Ran 12 tests in 0.055s / OK`、CLI exit `0`、safety assertions PASS、中文注释 `20.40%` | PASS / Engineer evidence accepted |
| vendor 事实与候选边界 | 本地 vendor source 可追溯，源码推断不冒充板上事实 | source hash/symbol/line 已冻结；primary=`encoder_update_path_not_observed`，status=`highest_priority_unconfirmed`，不是 encoder 损坏确认 | PASS |
| 远端只读 inventory | 一次 SSH、allowlist、逐命令 exit、零 mutation | inventory schema=`trashbot.wave_rover.readonly_runtime_inventory.v1`；5 类命令与 allowlist 一致且逐条 exit `0`；runtime `mainType` / firmware identity 均为 `not_observed` | PASS |
| 安全围栏 | 不运动、不改 service/UART/firmware | motion/control/stop/nonzero/service mutation/UART write/firmware mutation=`0/0/0/0/0/0/0`；HIL/safe/route/delivery 均 false | PASS |
| anti-repeat | v8 不复用，不包装同一动作窗口 | v8 authorization 仍为 `consumed_no_retry`；reuse/retry=`0/0`，本轮运动授权未消费 | PASS |
| OKR 增量 | supporting diagnostic 默认 flat | 接受 `current_run_artifact_delta=true`，只表示本轮实现、测试、3 artifacts、硬件文档与 current read-only inventory；不接受 mission/HIL/route/delivery credit | FLAT |

## Artifact 与结构验收

Product 只读解析并核对 `sprints/2026.07.21_08-50_o1_wheel_feedback_root_cause/` 的三个 artifact：

- `artifacts/root_cause_diagnostic.json`
- `artifacts/readonly_runtime_inventory.json`
- `artifacts/root_cause_diagnostic_with_inventory.json`

三个文件均通过 `python3 -m json.tool`。两个 diagnostic 的 schema、status、`input_valid=true`、有序 candidate 边界、唯一下一
动作和安全 false/零计数一致；带 inventory 版本为 `runtime_inventory_validation.status=valid_readonly_inventory`。inventory 的
schema、readonly allowlist、五条命令 exit `0`、`readonly_only=true` 与零 mutation 计数一致。Product 未重跑 Engineer tests、
SSH、HTTP、ROS、control、UART 或 firmware 命令。

## Product 方向与 proof boundary

用户价值/北极星仍是可信、安全、可解释的真实底盘控制与反馈闭环。本轮把“`T=11` 非零已发送但 `T=1001 L/R=0/0`”从
重复 motion 猜测收窄为可复验的诊断序列：先确认 runtime identity，再观察 raw encoder counter。Product 接受 proof
boundary=`offline_vendor_v8_diagnostic_plus_single_remote_readonly_inventory_supporting_only`。

该边界不证明 ESP32 deployed firmware 与本地 V0.9 一致，不证明 runtime `mainType`、raw encoder A/B counter delta、raw UART
timing、nonzero wheel feedback、HIL、safe-to-control、Nav2 route execution、delivery 或 Mission Objective 0。O1 保持约
`95%`，KR `不归档`、历史区无新增；O5 约 `85%` provider/runtime blocker `2/2` 继续暂停，O6/O7 各约 `93%` 的 corrected
Phase0 lane `2/2` 继续暂停。

## 唯一下一动作

`maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters`：取得独占 service/UART/firmware 维护授权后，先冻结
deployed ESP32 firmware identity 与 runtime `mainType`，再增加或读取 raw encoder A/B counter delta；在 counter path 可观测前
不批准新的 motion retry。任何 service stop/restart、UART claim、T=900 或 firmware instrumentation/flash 都需要新的明确维护
授权，不能复用本 sprint 或 v8 的授权。
