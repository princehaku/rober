# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - Tech Plan

## OKR 最低优先级核对

1. Live `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。理由：本机 Docker-only，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和真实 phone/browser external proof；继续本地 O5 metadata depth 不能推进 O5 completion。
3. 次低 Objective 1 约 81%，本 sprint 也不针对 Objective 1。理由：仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。本机没有真实硬件，不继续消费同一 blocker。
4. 本 sprint 针对 Objective 2 / Objective 3。理由：PR #4 已要求 elevator-assisted delivery 进入主链；上一轮 `elevator_field_evidence_trace_callback_intake` 只把 callback packet 收进同一 safe `evidence_ref`，下一步可执行抓手是 review decision，明确哪些材料仍缺、哪些材料被拒、是否需要重新回执或可进入 owner handoff。

## 技术目标

新增 `elevator_field_evidence_trace_callback_review_decision` software-proof chain。

能力边界：

- 读取上一轮 callback intake artifact、summary 或 wrapper/nested JSON。
- 校验 schema、boundary、source、same safe `evidence_ref`、unsafe copy、success/control claims。
- 根据 `intake_status`、`missing_required_materials`、`rejected_callback_materials` 和 same-ref 状态输出 review decision。
- Robot diagnostics 只读消费 summary alias。
- mobile/web 只读展示 decision、reasons、next required evidence、owner handoff。
- 全链保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 接口契约草案

Autonomy worker 输出 summary 语义如下；字段名可按现有风格微调，但语义不得放宽：

```json
{
  "schema": "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1",
  "source": "software_proof",
  "overall_status": "not_proven",
  "review_decision": "needs_route_elevator_material_backfill_not_proven",
  "safe_evidence_ref": "safe-field-owner-ref",
  "source_callback_intake": {
    "schema": "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1",
    "intake_status": "callback_packet_intake_ready_for_review_not_proven"
  },
  "decision_reasons": [
    "missing_real_nav2_or_fixed_route_runtime_log"
  ],
  "missing_required_materials": [
    "real_nav2_or_fixed_route_runtime_log"
  ],
  "rejected_callback_materials": [],
  "next_required_evidence": [
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_nav2_or_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result"
  ],
  "owner_handoff": [
    "Autonomy owner reviews route runtime and route completion material under the same evidence_ref.",
    "Robot owner reviews field task record and diagnostics summary under the same evidence_ref.",
    "Field owner backfills elevator door, target floor, assistance, dropoff/cancel, and delivery result materials."
  ],
  "delivery_success": false,
  "primary_actions_enabled": false,
  "not_proven": [
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success"
  ]
}
```

## 判定规则

- `blocked_missing_callback_intake_not_proven`：没有 intake artifact/summary 或 JSON 不可读。
- `blocked_unsupported_callback_intake_not_proven`：schema、boundary、source、overall status 或 required booleans 不符合上一轮 intake contract。
- `blocked_evidence_ref_mismatch_not_proven`：input/CLI 缺 safe ref、ref 不一致，或 `same_evidence_ref_required` 弱化。
- `blocked_unsafe_callback_review_copy_not_proven`：出现 raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、traceback、raw artifact、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true`。
- `needs_callback_packet_rerun_not_proven`：上一轮 intake status 不是 ready，或仍缺 safe callback packet。
- `needs_route_elevator_material_backfill_not_proven`：intake ready 但缺真实 route/elevator material，或存在 rejected callback material。
- `ready_for_elevator_field_owner_handoff_not_proven`：intake ready、same-ref 对齐、材料列表完整且无 rejected material；仍只是 owner handoff ready，不是真实 field pass。

## Owner 分工和文件范围

下面 3 个 owner 文件范围互不重叠，必须并行启动 worker；Product 在实现完成后 closeout。

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| autonomy-engineer | `pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py`、`tests/test_elevator_field_evidence_trace_callback_review_decision.py`、`docs/interfaces/elevator_field_evidence_trace_callback_review_decision.md`、本 sprint `tech-done.md` 中 Autonomy 小节 | 实现 PC review-decision gate、same-ref/unsafe/decision mapping、focused unittest、interface docs |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/operator_gateway_diagnostics.md`、本 sprint `tech-done.md` 中 Robot 小节 | 增加 `robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary` safe alias，只读消费 summary，缺 summary fail closed |
| full-stack-software-engineer | `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中 Full-Stack 小节 | 新增 mobile/web 只读 panel 和 fixture，展示 review decision、reasons、next evidence、owner handoff，不改变 Start Delivery / Confirm Dropoff / Cancel gating |
| product-okr-owner | 实现完成后：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `side2side_check.md`、本 sprint `final.md` | 验收 Product/OKR 边界；只按真实验证结果更新进度，不把 planning 或 software proof 写成实机完成 |

## 接口影响

- 新增 PC evidence summary schema：`trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary`。
- mobile/web 只读消费该 alias 或 fixture 字段；不得新增控制 API 或 action command。
- 不修改 `TrashCollection` action schema，不修改 `/cmd_vel`、serial/UART、hardware launch 参数，不修改 cloud relay command contract。

## 子 agent 执行提示

实现阶段主节点必须按 AGENTS 固定结构派发 worker，prompt 需包含对应 `.codex/agents/<role>.toml` 的完整 System Prompt，并明确“你不是独自在代码库中工作，不要回滚其他 worker 或用户改动”。

虽然本 sprint 不改硬件，所有 worker 仍必须避免引入 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸、2D LiDAR/ToF SKU 或 HIL-entry 的新事实；如果实现触及硬件事实，必须先读 `docs/vendor/VENDOR_INDEX.md`，并只引用本地 vendor/source 边界。

## 验收命令

### Autonomy worker

```bash
python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py
python3 -m unittest tests/test_elevator_field_evidence_trace_callback_review_decision.py
rg -n "elevator_field_evidence_trace_callback_review_decision|elevator_field_evidence_trace_callback_intake|safe_evidence_ref|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_elevator_field_owner_handoff_not_proven|needs_route_elevator_material_backfill_not_proven" pc-tools/evidence tests docs/interfaces/elevator_field_evidence_trace_callback_review_decision.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
git diff --check -- pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py tests/test_elevator_field_evidence_trace_callback_review_decision.py docs/interfaces/elevator_field_evidence_trace_callback_review_decision.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
```

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary|elevator_field_evidence_trace_callback_review_decision|elevator_field_evidence_trace_callback_intake|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_field_evidence_trace_callback_review_decision|elevator_field_evidence_trace_callback_intake|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|review_decision|decision_reasons|next_required_evidence|owner_handoff" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
```

### Product planning gate

```bash
test -f sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/pre_start.md && test -f sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/prd.md && test -f sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|Objective 2|Objective 3|PR #4|PR #5|elevator_field_evidence_trace_callback_review_decision|elevator_field_evidence_trace_callback_intake|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
git diff --check -- sprints/2026.05.19_05-06_elevator-field-evidence-trace-callback-review-decision
```

## 风险边界

- 本 sprint planning 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，不更新 `OKR.md`，不更新产品代码。
- 后续 implementation 只能算 Docker/local `software_proof`。即使所有 worker 验证通过，也不证明真实电梯、真实 Nav2/fixed-route、真实 task record、真实 route completion、真实 dropoff/cancel、delivery success、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料或 O5 external proof。
- 如果 review decision input 不是上一轮 safe/redacted intake summary，必须输出 blocked；不得在 Robot/mobile 展示原始内容。

## 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时创建 `side2side_check.md` 和 `final.md`，并按实际结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- OKR closeout 只能记录 callback review decision software-proof 可判定性；不得提高 Objective 5 external proof、Objective 1 HIL/hardware pass，也不得把 Objective 2 / Objective 3 写成真实 field pass。
