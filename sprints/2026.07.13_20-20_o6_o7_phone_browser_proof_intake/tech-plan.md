# Tech Plan - O6/O7 Phone Browser Proof Intake

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低完成度 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接推进 O5。
3. 切换理由：最新 O5 sprint 已 blocked 在 `blocked_http_status_not_success_class`，且 19:19 已消费 readiness packet。当前没有 success-class public endpoint、production DB/queue、worker cutover、OSS/CDN origin fetch/upload、4G/SIM 或 real phone/browser 证据；继续 O5 会重复 CDN/TLS probe、readiness packet 或 support-only wrapper。

## Owner Routing

主责 owner：`full-stack-software-engineer`。

协作 owner：`robot-software-engineer`。

路由理由：O7 selected-task action/UI/receipt 是用户触点主路径；O6 archive/readback section 是同一 `task_id` 的数据源合同。两个 owner 文件范围互不重叠，进入 implementation 时应并行派发；若运行时只能单线，则由 `full-stack-software-engineer` 主责集成，`robot-software-engineer` 先给 O6 合同事实。

## Technical Approach

新增 O6/O7 phone-browser terminal-material intake：

- O6 增加 `phone_browser_terminal_material` consumer detail section，或等价 alias。
- O7 增加 `POST /api/o7/consumer-read/tasks/:taskId/phone-browser-proof/intake?baseUrl=<local-loopback-url>`。
- O7 adapter 将 selected task 的安全 phone/browser material 摘要写入 O6，并立即读取/返回 safe receipt。
- Proof boundary 固定为 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`。
- 所有成功和失败输出都固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`、`robot_control_executed=false`。

## File Scope

Robot Software owner 允许改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

Full-stack owner 允许改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

Sprint doc 允许改：

- `sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/tech-done.md`
- Epic closeout 后续再写 `side2side_check.md`、`final.md`。

禁止改：

- 硬件/vendor 文件。
- WAVE ROVER、ESP32、Orange Pi、UART、串口、波特率、引脚、电压或机械配置。
- ROS2 launch、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART。
- O5 CDN/TLS probe、O5 readiness packet consumption、历史 sprint 文件、`docs/process/okr_progress_log.md`。

## Interface Contract

O6 section suggested shape:

```json
{
  "schema": "trashbot.o6.phone_browser_terminal_material.v1",
  "status": "phone_browser_terminal_material_ready_not_delivery_proof",
  "proof_scope": "software_proof_o6_o7_phone_browser_terminal_material_intake_only",
  "task_id": "<same task>",
  "safe_evidence_ref": "<safe ref>",
  "accepted_materials": ["true_phone_browser_evidence", "diagnostics_mobile_safe_summary"],
  "missing_materials": ["verified_terminal_result_or_delivery_acceptance"],
  "safe_to_control": false,
  "delivery_success": false,
  "route_execution_success": false,
  "hil_pass": false,
  "connects_cloud_production": false
}
```

O7 receipt suggested shape:

```json
{
  "schema": "trashbot.pc_tools_workstation.o7_phone_browser_proof_intake_result.v1",
  "status": "local_mock_phone_browser_material_written",
  "proof_scope": "software_proof_o6_o7_phone_browser_terminal_material_intake_only",
  "same_task_id_consumed": true,
  "phone_browser_terminal_material_written": true,
  "phone_browser_terminal_material_readback": true,
  "safe_to_control": false,
  "delivery_success": false,
  "route_execution_success": false,
  "hil_pass": false,
  "connects_cloud_production": false
}
```

## Acceptance Commands

Robot Software owner 必须运行并记录：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
rg -n "phone_browser_terminal_material|true_phone_browser_evidence|software_proof_o6_o7_phone_browser_terminal_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false" onboard/src/ros2_trashbot_behavior docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/tech-done.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake
```

Full-stack owner 必须运行并记录：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "phone-browser-proof/intake|o7_phone_browser_proof_intake|phone_browser_terminal_material|software_proof_o6_o7_phone_browser_terminal_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false" pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/tech-done.md
git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake
```

Product plan-only validation:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|blocked_http_status_not_success_class|software_proof|safe_to_control=false|delivery_success=false" sprints/2026.07.13_20-20_*/pre_start.md sprints/2026.07.13_20-20_*/prd.md sprints/2026.07.13_20-20_*/tech-plan.md
git diff --check -- sprints/2026.07.13_20-20_* OKR.md
```

## Risks

- 该路径仍可能只是 local/mock software proof，不会提升 O5/O6/O7 主百分比。
- 如果 O6/O7 只写 receipt 而没有同一 `task_id` readback，Product 不应接受。
- 如果 receipt 接受 raw URL、cookie、token、本地路径、DOM dump、截图 body、`delivery_success=true` 或任何 control/HIL true 字段，必须 fail closed 并返工。
- 真实 phone/browser acceptance 需要后续真实设备、生产云入口、任务终态和 operator 验收材料，不在本计划阶段证明。
