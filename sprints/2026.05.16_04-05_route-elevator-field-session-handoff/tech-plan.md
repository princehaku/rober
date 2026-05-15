# Sprint 2026.05.16_04-05 Route Elevator Field Session Handoff - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `route_elevator_field_session_handoff`，证据边界固定为 `software_proof_docker_route_elevator_field_session_handoff_gate`。它位于上一轮 PC route elevator console integration 之后，负责把 PC route debug console summary、route completion signal、elevator-route reconciliation summary 和下一次现场 session 的采集清单打包为同一 `evidence_ref` 的 handoff artifact/summary。

该 gate 只读本机 JSON artifact 或 summary，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。所有下游消费都必须 metadata-only、read-only、fail-closed。

## 2. 接口契约

### Artifact

- `schema=trashbot.route_elevator_field_session_handoff.v1`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_elevator_field_session_handoff_gate`
- `same_evidence_ref_required=true`
- `evidence_ref=<safe evidence ref>`
- `handoff_verdict=<ready_for_field_session_handoff_not_proven | blocked_missing_inputs | blocked_evidence_ref_mismatch | blocked_invalid_input | blocked_unsafe_copy | blocked_success_claim>`
- `source_summaries.pc_route_debug_console`
- `source_summaries.route_completion_signal`
- `source_summaries.elevator_route_reconciliation`
- `field_session_manifest`
- `required_materials`
- `operator_handoff`
- `robot_diagnostics_summary`
- `mobile_readonly_summary`
- `not_proven`
- `primary_actions_enabled=false`
- `delivery_success=false`

### Summary

- `schema=trashbot.route_elevator_field_session_handoff_summary.v1`
- `evidence_boundary=software_proof_docker_route_elevator_field_session_handoff_gate`
- `handoff_verdict`
- safe `evidence_ref`
- `same_evidence_ref_required=true`
- `required_materials_summary`
- `operator_next_steps`
- `not_proven`
- `primary_actions_enabled=false`
- `delivery_success=false`

### 必填现场材料清单

`required_materials` 至少覆盖：

- `nav2_fixed_route_runtime_log.json`
- `route_completion_signal.json`
- `task_record.json`
- `door_state.json`
- `target_floor_confirmation.json`
- `human_assistance_operator_note.md`
- `dropoff_or_cancel_completion.json`
- `delivery_result.json`
- `diagnostics_mobile_safe_summary.json`

这些材料必须使用同一 safe `evidence_ref`。本轮 CLI 可以生成 checklist/manifest，但不能把 checklist 存在写成真实材料已通过。

## 3. 任务拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_elevator_field_session_handoff.py`
- `pc-tools/evidence/test_route_elevator_field_session_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 CLI `pc-tools/evidence/route_elevator_field_session_handoff.py`。
- CLI 接受 `--pc-route-debug-json`、`--route-completion-json`、`--elevator-route-reconciliation-json`、`--evidence-ref`、`--output`，可选 `--summary-output`、`--session-id`、`--operator`、`--location`、`--time-window`。
- 支持输入 artifact 或 summary；unsupported schema/boundary/source、坏 JSON、缺输入、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或成功文案必须 fail closed。
- 输出 artifact + summary，字段遵循本 plan 第 2 节契约。
- `robot_diagnostics_summary` 和 `mobile_readonly_summary` 必须是白名单摘要，不能包含 raw artifact、完整本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。
- docs 说明该 gate 是现场 session handoff，不是 delivery success，也不是 Objective 5 external proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_elevator_field_session_handoff.py pc-tools/evidence/test_route_elevator_field_session_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_elevator_field_session_handoff.py
python3 pc-tools/evidence/route_elevator_field_session_handoff.py --help
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_elevator_field_session_handoff.py pc-tools/evidence/test_route_elevator_field_session_handoff.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- diagnostics 新增 metadata-only 消费字段 `route_elevator_field_session_handoff`。
- 只接受 `trashbot.route_elevator_field_session_handoff.v1` 或 `trashbot.route_elevator_field_session_handoff_summary.v1` 的白名单摘要。
- 缺失、bad schema/boundary、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或成功文案时返回 blocked/not_proven summary。
- 不改变 `/api/collect`、ACK、cursor、Nav2、dropoff/cancel、route execution 或 HIL 行为。
- 文档说明该 diagnostics 字段只用于现场 session handoff 解释，不是控制授权。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|delivery_success|primary_actions_enabled|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- mobile/web 新增只读 “路线电梯现场交接” panel。
- 从 `/api/status`、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary` 或 nested diagnostics summary 中读取 `route_elevator_field_session_handoff` / `route_elevator_field_session_handoff_summary`。
- 展示 handoff verdict、safe `evidence_ref`、same-evidence-ref 状态、required materials summary、operator next steps、boundary、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- 缺 summary 时显示 blocked/not_proven。
- 不 fetch raw artifact，不显示本机路径、checksum、traceback、raw ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、凭证、DB/queue URL、OSS/CDN 材料。
- Start / Confirm Dropoff / Cancel 继续只由既有 `command_safety` 和 legacy gates 控制，不能因 handoff summary 启用。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Product Closeout - Product Manager / OKR Owner

文件范围：

- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/tech-done.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/side2side_check.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Task A/B/C 的实际改动、验证结果和偏差。
- `final.md` 必须明确：本轮证据是 `software_proof_docker_route_elevator_field_session_handoff_gate`，不是真实 route/elevator field pass。
- `OKR.md` 只可保守更新 Objective 2/3 的支撑说明；如果没有真实现场材料，不得上调 O5，也不得写 delivery success。
- `docs/process/okr_progress_log.md` 顶部追加本轮记录。

验收命令：

```bash
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|Objective 2|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_04-05_route-elevator-field-session-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_04-05_route-elevator-field-session-handoff OKR.md docs/process/okr_progress_log.md
```

## 4. 并行启动要求

本轮是跨 owner epic sprint，文件范围互不重叠，默认并行启动三个 Engineer 子 agent：

- Autonomy Algorithm Engineer 执行 Task A。
- Robot Platform Engineer 执行 Task B。
- User Touchpoint Full-Stack Engineer 执行 Task C。

Task B/C 可在 Task A schema 稳定后按本 tech-plan 的接口契约实现；若 Task A 最终字段名偏离第 2 节，Task A 必须在返回中明确偏差，Product Closeout 再要求 B/C 对齐或返工。

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对该最低 Objective：否。
3. 具体理由：Objective 5 当前剩余可推进 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据；本机当前只有 Docker/local software proof，继续做 O5 metadata 会重复消费同一外部证据 blocker。`OKR.md` 第 6 节已经明确要求不要重复本地 O5 metadata depth，并把当前最高可行动作指向 Objective 3/O2 的 route/elevator 真实现场/上车复账链路。本轮 `route_elevator_field_session_handoff` 正是为同一 `evidence_ref` 的现场材料回填做交接，不声明真实送达。

## 6. 风险边界

- 本轮只证明 Docker/local handoff artifact/summary 可生成、可被 diagnostics/mobile 只读消费。
- 不证明真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 task record、真实电梯门状态、真实目标楼层确认、真实人工协助、真实 dropoff/cancel completion、真实 delivery result、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 所有新增文案必须保持 read-only、not_proven、`primary_actions_enabled=false` 和 `delivery_success=false`。
- 本轮不新增硬件参数、串口、波特率、引脚、电压、固件或机械安装假设；若后续 Task 触碰这些内容，必须先查 `docs/vendor/VENDOR_INDEX.md`。

## 7. 本计划验收命令

```bash
rg -n "route_elevator_field_session_handoff|software_proof_docker_route_elevator_field_session_handoff_gate|Objective 5|OKR 最低优先级核对|sprint_type: epic" sprints/2026.05.16_04-05_route-elevator-field-session-handoff
git diff --check -- sprints/2026.05.16_04-05_route-elevator-field-session-handoff
```
