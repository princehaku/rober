# Sprint 2026.05.19_06-07 Elevator Field Evidence Trace Callback Review Handoff - Tech Plan

## OKR 最低优先级核对

1. Live `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。理由：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、真实手机/browser external proof；本机 Docker-only 只能做 local metadata，继续 O5 wrapper 不能推进 O5 completion。
3. 次低 Objective 1 约 81%，本 sprint 也不针对 Objective 1。理由：仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；无真实硬件和真实材料时，不重复消费同一 blocker。
4. 本 sprint 针对 Objective 2 / Objective 3，并触达 Objective 4 只读展示。理由：PR #4 / PR #5 GitHub review 证据显示 elevator-assisted delivery mandatory，硬件 baseline/source/material 仍是缺口；最近两轮已经完成 `elevator_field_evidence_trace_callback_intake` 与 `elevator_field_evidence_trace_callback_review_decision`，下一步可执行抓手是 `elevator_field_evidence_trace_callback_review_handoff`，把 review decision 变成 owner handoff package。

## 技术目标

新增 `elevator_field_evidence_trace_callback_review_handoff` software-proof chain。

能力边界：

- 输入上一轮 `elevator_field_evidence_trace_callback_review_decision` artifact、summary 或 diagnostics wrapper。
- 校验 schema、source、boundary、same safe `evidence_ref`、unsupported status 和 unsafe copy。
- 输出 owner handoff package，分发 Autonomy、Robot、Full-Stack、Field owner 下一步责任。
- Robot diagnostics 只读消费 handoff summary alias。
- mobile/web 只读展示 handoff package，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 全链保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 接口契约草案

Autonomy worker 输出 summary 语义如下；字段名可按现有风格微调，但语义不得放宽：

```json
{
  "schema": "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1",
  "source": "software_proof",
  "overall_status": "not_proven",
  "handoff_status": "ready_for_owner_material_backfill_not_proven",
  "safe_evidence_ref": "safe-field-owner-ref",
  "source_review_decision": {
    "schema": "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1",
    "review_decision": "ready_for_elevator_field_owner_handoff_not_proven"
  },
  "owner_handoff": {
    "autonomy": [
      "Review real Nav2/fixed-route runtime log under the same evidence_ref.",
      "Review route completion signal under the same evidence_ref."
    ],
    "robot": [
      "Review field task record and diagnostics same-ref summary.",
      "Keep robot diagnostics read-only and fail-closed."
    ],
    "full_stack": [
      "Render phone-safe handoff package without enabling primary actions.",
      "Keep Start Delivery, Confirm Dropoff, and Cancel gating unchanged."
    ],
    "field_owner": [
      "Backfill real elevator door state.",
      "Backfill real target floor confirmation.",
      "Backfill real human assistance record.",
      "Backfill real dropoff/cancel completion and delivery result."
    ]
  },
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
  "next_required_evidence": [
    "same_evidence_ref_real_field_material_backfill"
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

- `blocked_missing_review_decision_not_proven`：没有 review decision artifact/summary 或 JSON 不可读。
- `blocked_unsupported_review_decision_not_proven`：schema、source、overall status、evidence boundary 或 required booleans 不符合上一轮 review decision contract。
- `blocked_evidence_ref_mismatch_not_proven`：input/CLI 缺 safe ref、ref 不一致，或 same-ref 要求被弱化。
- `blocked_unsafe_handoff_copy_not_proven`：出现 raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、traceback、raw artifact、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true`。
- `needs_review_decision_rerun_not_proven`：source review decision 不是可 handoff / backfill 的 supported status。
- `ready_for_owner_material_backfill_not_proven`：source review decision 可进入 owner handoff，但仍缺真实 route/elevator material。
- `ready_for_field_execution_owner_handoff_not_proven`：source review decision、same-ref、material checklist 均完整，仍只是 owner handoff ready，不是真实 route/elevator field pass。

## Owner 分工和文件范围

下面 3 个 owner 文件范围互不重叠，implementation 阶段必须并行启动 worker；Product closeout 后置。

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| autonomy-engineer | `pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py`、`tests/test_elevator_field_evidence_trace_callback_review_handoff.py`、`docs/interfaces/elevator_field_evidence_trace_callback_review_handoff.md`、本 sprint `tech-done.md` 中 Autonomy 小节 | 实现 PC handoff package gate、same-ref/unsafe/handoff mapping、focused unittest、interface docs |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/operator_gateway_diagnostics.md`、本 sprint `tech-done.md` 中 Robot 小节 | 增加 `robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary` safe alias，只读消费 summary，缺 summary fail closed |
| full-stack-software-engineer | `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中 Full-Stack 小节 | 新增 mobile/web 只读 panel 和 fixture，展示 handoff status、owner handoff、missing materials、next evidence，不改变 Start Delivery / Confirm Dropoff / Cancel gating |
| product-okr-owner | 实现完成后：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `side2side_check.md`、本 sprint `final.md` | 验收 Product/OKR 边界；只按真实验证结果更新进度，不把 planning 或 software proof 写成实机完成 |

## 接口影响

- 新增 PC evidence summary schema：`trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary`。
- mobile/web 只读消费该 alias 或 fixture 字段。
- 不修改 `TrashCollection` action schema，不修改 `/cmd_vel`、serial/UART、hardware launch 参数，不修改 cloud relay command contract。
- 不新增真实硬件事实；若 implementation 触及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸、2D LiDAR / ToF SKU 或 HIL-entry，worker 必须先读 `docs/vendor/VENDOR_INDEX.md` 并引用本地资料来源。

## 子 agent 执行提示

实现阶段主节点必须按 AGENTS 固定结构派发 worker，prompt 需包含对应 `.codex/agents/<role>.toml` 的完整 System Prompt，并明确“你不是独自在代码库中工作，不要回滚其他 worker 或用户改动”。

本 sprint 文件范围跨 Autonomy、Robot、Full-Stack 且互不重叠，必须同一轮并行启动 3 个 worker。Product 不在 implementation 前创建 `tech-done.md`、`side2side_check.md`、`final.md`，也不提前更新 `OKR.md`。

## 验收命令

### Autonomy worker

```bash
python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py
python3 -m unittest tests/test_elevator_field_evidence_trace_callback_review_handoff.py
rg -n "elevator_field_evidence_trace_callback_review_handoff|elevator_field_evidence_trace_callback_review_decision|safe_evidence_ref|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_owner_material_backfill_not_proven|ready_for_field_execution_owner_handoff_not_proven" pc-tools/evidence tests docs/interfaces/elevator_field_evidence_trace_callback_review_handoff.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
git diff --check -- pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py tests/test_elevator_field_evidence_trace_callback_review_handoff.py docs/interfaces/elevator_field_evidence_trace_callback_review_handoff.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
```

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary|elevator_field_evidence_trace_callback_review_handoff|elevator_field_evidence_trace_callback_review_decision|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_field_evidence_trace_callback_review_handoff|elevator_field_evidence_trace_callback_review_decision|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|handoff_status|owner_handoff|next_required_evidence" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
```

### Product planning gate

```bash
test -f sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff/pre_start.md && test -f sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff/prd.md && test -f sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|Objective 2|Objective 3|PR #4|PR #5|elevator_field_evidence_trace_callback_review_handoff|elevator_field_evidence_trace_callback_review_decision|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
git diff --check -- sprints/2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff
```

## 风险边界

- 本 sprint planning 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，不更新 `OKR.md`，不更新产品代码或测试。
- 后续 implementation 只能算 Docker/local `software_proof`。即使所有 worker 验证通过，也不证明真实电梯、真实 Nav2/fixed-route、真实 task record、真实 route completion、真实 dropoff/cancel、delivery success、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料或 O5 external proof。
- 如果 source review decision 不是上一轮 safe/redacted summary，必须输出 blocked；不得在 Robot/mobile 展示原始内容。

## 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时创建 `side2side_check.md` 和 `final.md`，并按实际结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- OKR closeout 只能记录 callback review handoff package 的 `software_proof` 可交接性；不得提高 Objective 5 external proof、Objective 1 HIL/hardware pass，也不得把 Objective 2 / Objective 3 写成真实 field pass。
