# Sprint 2026.05.19_04-05 Elevator Field Evidence Trace Callback Intake - Tech Plan

## OKR 最低优先级核对

1. Live `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。理由：本机是 Docker-only，仍缺真实 HTTPS/TLS、公网 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和 real phone/browser external proof；继续本地 O5 wrapper 不能推进 O5 completion。
3. 次低 Objective 1 约 81%，本 sprint 也不针对 Objective 1。理由：PR #5 closeout gate 已处理 review thread 的 mainline docs 可判定性，但真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍不可用。本机没有真实硬件，不第三次消费同一硬件 blocker。
4. 本 sprint 针对 Objective 2 / Objective 3。理由：PR #4 已合并并要求 elevator-assisted delivery 进入主链；`2026.05.19_00-01` 和 `2026.05.19_02-03` 已完成 `elevator_action_feedback_trace` 的实时 feedback 与 post-run task_record/diagnostics/mobile trace，但 final 仍明确缺真实 route/elevator field materials。下一步可执行抓手是 `elevator_field_evidence_trace_callback_intake`，把未来现场 owner 的安全 callback packet 和现有 trace/summary/material requirements 做同一 safe `evidence_ref` 的只读 intake 判定。

## 技术目标

实现阶段目标：新增 `elevator_field_evidence_trace_callback_intake` software-proof chain。

能力边界：

- 读取 safe callback packet、`elevator_action_feedback_trace` summary、diagnostics/mobile summary、route/elevator required materials。
- 校验同一 safe `evidence_ref`。
- 输出 intake artifact 和 sanitized summary。
- Robot diagnostics 只读消费 summary alias。
- mobile/web 只读展示 intake status、missing materials、owner handoff。
- 全链保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 接口契约草案

建议 Autonomy worker 输出 summary 结构如下；worker 可按现有代码风格微调字段名，但语义不得放宽：

```json
{
  "schema": "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1",
  "source": "software_proof",
  "overall_status": "not_proven",
  "intake_status": "needs_route_elevator_material_backfill_not_proven",
  "evidence_ref": "safe-field-owner-ref",
  "source_trace": {
    "schema": "trashbot.elevator_action_feedback_trace_summary.v1",
    "trace_status": "software_trace_ready"
  },
  "source_diagnostics": {
    "alias": "robot_diagnostics_elevator_action_feedback_trace_summary",
    "summary_status": "not_proven"
  },
  "callback_packet": {
    "packet_status": "callback_packet_metadata_received_not_proven",
    "redaction_status": "redacted",
    "owner_acknowledgement": "field_owner_acknowledges_real_materials_still_required"
  },
  "accepted_callback_materials": [
    "safe_evidence_ref",
    "redacted_callback_packet_metadata",
    "trace_summary_ref",
    "owner_acknowledgement"
  ],
  "missing_required_materials": [
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_nav2_or_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result"
  ],
  "not_proven": [
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success"
  ],
  "delivery_success": false,
  "primary_actions_enabled": false,
  "owner_handoff": [
    "Autonomy owner backfills route runtime and completion materials under the same evidence_ref.",
    "Robot owner backfills field task record and diagnostics summary under the same evidence_ref.",
    "Field owner backfills elevator door, target floor, assistance, dropoff/cancel, and delivery result materials."
  ]
}
```

## 判定规则

- `blocked_missing_callback_packet_not_proven`：没有 callback packet 或 packet schema 不匹配。
- `blocked_evidence_ref_mismatch_not_proven`：callback packet、trace summary、diagnostics/mobile summary、required materials 中的 `evidence_ref` 缺失、不安全或不一致。
- `needs_route_elevator_material_backfill_not_proven`：packet 安全且 trace 对齐，但真实 route/elevator materials 仍缺。
- `callback_packet_intake_ready_for_review_not_proven`：packet 安全、same `evidence_ref` 对齐、required material list 完整记录；仍不代表真实 field pass，下一轮进入 review decision。

Fail-closed 规则：

- `delivery_success` 与 `primary_actions_enabled` 必须是布尔 false。
- `source` 只能是 `software_proof`，不能出现 `hil_pass`、`field_pass`、`production_ready` 或 `delivery_success=true`。
- 出现 raw ROS topic、`/cmd_vel`、串口设备、波特率、WAVE ROVER 参数、凭证、本机绝对路径、traceback、完整内部日志或 raw callback body 时，gate 必须 fail closed 或 redaction fail。
- 不得从 `elevator_action_feedback_trace` 反推真实 route/elevator field pass。

## Owner 分工和文件范围

进入实现阶段时，下面 3 个 owner 文件范围互不重叠，必须同一轮并行启动 3 个 worker。Product 只在实现完成后 closeout。

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| autonomy-engineer | `pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py`、`tests/test_elevator_field_evidence_trace_callback_intake.py`、`docs/interfaces/elevator_field_evidence_trace_callback_intake.md`、本 sprint `tech-done.md` 中 Autonomy 小节 | 实现 PC evidence gate、sample callback packet / trace summary fixtures、same `evidence_ref` 判定、focused unittest、interface docs |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/operator_gateway_diagnostics.md`、本 sprint `tech-done.md` 中 Robot 小节 | 增加 `robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary` safe alias，只读消费 summary，缺 summary fail closed |
| full-stack-software-engineer | `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中 Full-Stack 小节 | 新增 mobile/web 只读 panel 和 fixture，展示 intake status、missing materials、owner handoff，不改变 Start Delivery / Confirm Dropoff / Cancel gating |
| product-okr-owner | 实现完成后：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `side2side_check.md`、本 sprint `final.md` | 验收 Product/OKR 边界；只按真实验证结果更新进度，不把 planning 或 software proof 写成实机完成 |

## 接口影响

- 新增 PC evidence summary schema：`trashbot.elevator_field_evidence_trace_callback_intake_summary.v1`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary`。
- mobile/web 只读消费该 alias 或 fixture 字段；不得新增控制 API 或 action command。
- 不修改 `TrashCollection` action schema，不修改 `/cmd_vel`、serial/UART、hardware launch 参数，不修改 cloud relay command contract。

## 子 agent 执行提示

实现阶段主节点必须按 AGENTS 固定结构派发 worker，prompt 需包含对应 `.codex/agents/<role>.toml` 的完整 System Prompt，并明确“你不是独自在代码库中工作，不要回滚其他 worker 或用户改动”。

虽然本 sprint 不改硬件，所有 worker 仍必须避免引入 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸、2D LiDAR/ToF SKU 或 HIL-entry 的新事实；如果实现触及硬件事实，必须先读 `docs/vendor/VENDOR_INDEX.md`，并只引用本地 vendor/source 边界。

## 验收命令

### Autonomy worker

```bash
python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py
python3 -m unittest tests/test_elevator_field_evidence_trace_callback_intake.py
rg -n "elevator_field_evidence_trace_callback_intake|elevator_action_feedback_trace|safe_evidence_ref|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|real_route_elevator_field_pass|callback_packet_intake_ready_for_review_not_proven" pc-tools/evidence tests docs/interfaces/elevator_field_evidence_trace_callback_intake.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
git diff --check -- pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py tests/test_elevator_field_evidence_trace_callback_intake.py docs/interfaces/elevator_field_evidence_trace_callback_intake.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
```

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary|elevator_field_evidence_trace_callback_intake|elevator_action_feedback_trace|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_field_evidence_trace_callback_intake|elevator_action_feedback_trace|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|missing_required_materials|owner_handoff" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
```

### Product planning gate

```bash
test -f sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/pre_start.md && test -f sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/prd.md && test -f sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|Objective 2|Objective 3|PR #4|PR #5|elevator_field_evidence_trace_callback_intake|elevator_action_feedback_trace|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
git diff --check -- sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake
```

## 风险边界

- 本 sprint planning 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，不更新 `OKR.md`，不更新代码、测试或 docs。
- 后续 implementation 只能算 Docker/local `software_proof`。即使所有 worker 验证通过，也不证明真实电梯、真实 Nav2/fixed-route、真实 task record、真实 route completion、真实 dropoff/cancel、delivery success、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料或 O5 external proof。
- 如果 implementation 需要跨 owner 改同一个 docs 文件，必须先在 worker prompt 里调整文件边界；不得并行写同一文档导致覆盖。
- 如果 callback packet 不是 safe/redacted metadata，必须输出 redaction blocked；不得在 Robot/mobile 展示原始内容。

## 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时创建 `side2side_check.md` 和 `final.md`，并按实际结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- OKR closeout 只能记录 callback intake software-proof 可判定性；不得提高 Objective 5 external proof、Objective 1 HIL/hardware pass，也不得把 Objective 2 / Objective 3 写成真实 field pass。
