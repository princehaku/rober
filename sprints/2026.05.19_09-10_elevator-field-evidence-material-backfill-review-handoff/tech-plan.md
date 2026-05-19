# Sprint 2026.05.19_09-10 Elevator Field Evidence Material Backfill Review Handoff - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。理由：O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、真实手机/browser 或其他真实 external proof；本机只有 Docker，继续本地 O5 wrapper 不能提高 O5 completion，且会重复 metadata depth。
3. 次低 Objective 1 约 81%，本 sprint 也不直接针对 Objective 1。理由：O1 仍缺真实 WAVE ROVER/UART/HIL、真实串口日志、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；本轮没有真实硬件或真实材料，不能重复消费该 blocker。
4. 本 sprint 选择 Objective 2 / Objective 3，并触达 Objective 4 只读展示。理由：PR #4 已将 elevator-assisted delivery 固化为主链路；PR #5 固化硬件边界和 2D LiDAR / ToF 真实材料缺口；最近 `07-08` 和 `08-09` 已完成 material backfill intake -> review decision，下一步可在 Docker-only 主机上推进现场 owner handoff，同时不弱化 O5/O1 的真实材料边界。

## 1. 技术目标

规划 `elevator_field_evidence_trace_material_backfill_review_handoff` software-proof chain。

目标能力：

- 消费上一轮 `elevator_field_evidence_trace_material_backfill_review_decision` artifact / summary / Robot diagnostics safe alias。
- 校验 review decision schema、boundary、source、overall status、same safe `evidence_ref`、safe copy、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 边界。
- 基于 decision reasons、missing/rejected materials、next required evidence 和 existing owner handoff 输出现场 owner handoff package。
- 输出 safe rerun hints 和 phone-safe copy，明确下一步真实材料补齐动作。
- 输出可供 Robot diagnostics 和 mobile/web 只读消费的 summary。
- 为后续现场 owner 补材料和 rerun 准备，不声明真实 field pass。

## 2. 接口契约草案

Autonomy worker 输出 artifact 与 summary，字段名可按现有代码风格微调，但语义不得放宽。

```json
{
  "schema": "trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1",
  "source": "software_proof",
  "overall_status": "not_proven",
  "handoff_status": "ready_for_field_owner_material_backfill_rerun_not_proven",
  "safe_evidence_ref": "safe-field-owner-ref",
  "same_evidence_ref_required": true,
  "same_evidence_ref_status": "matched",
  "source_review_decision": {
    "schema": "trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1",
    "review_decision": "needs_required_material_backfill_not_proven",
    "evidence_boundary": "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate"
  },
  "field_owner_handoff": [
    {
      "owner": "field-owner",
      "required_material": "real_nav2_or_fixed_route_runtime_log",
      "next_action": "collect_same_evidence_ref_material_then_rerun_review_decision_and_handoff",
      "status": "not_proven"
    }
  ],
  "safe_rerun_hints": [
    "use_the_same_safe_evidence_ref",
    "provide_only_redacted_material_refs_to_robot_and_mobile",
    "rerun_review_decision_before_claiming_ready"
  ],
  "phone_safe_copy": [
    "现场材料仍未证明真实通过，请补齐同一证据编号下的真实路线、电梯和投放材料。"
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
  "rejected_materials": [],
  "delivery_success": false,
  "primary_actions_enabled": false,
  "not_proven": [
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success"
  ]
}
```

## 3. 判定规则

- `blocked_missing_material_backfill_review_decision_not_proven`：缺上一轮 review decision artifact/summary 或 JSON 不可读。
- `blocked_unsupported_material_backfill_review_decision_not_proven`：review decision schema、source、overall status、evidence boundary、same-ref 布尔或 required booleans 不符合 `elevator_field_evidence_trace_material_backfill_review_decision` contract。
- `blocked_evidence_ref_mismatch_not_proven`：CLI/source/diagnostics safe ref 缺失、不一致，或 `same_evidence_ref_required` 被弱化。
- `blocked_unsafe_material_review_handoff_not_proven`：review decision、handoff copy、safe rerun hints 或 phone-safe copy 出现 raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、complete raw artifact、traceback、success wording、`delivery_success=true` 或 `primary_actions_enabled=true`。
- `needs_field_owner_material_handoff_not_proven`：review decision 安全但 owner/action/material list 不完整，无法交给现场 owner。
- `ready_for_field_owner_material_backfill_rerun_not_proven`：handoff package 安全齐全，可进入现场 owner 补材料与 rerun；仍不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 4. Owner / File Scope

后续 implementation 文件范围跨 3 个 owner 且互不重叠，必须并行启动 3 个 worker。Product closeout 后置。

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| autonomy-engineer | `pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_handoff.py`、`tests/test_elevator_field_evidence_trace_material_backfill_review_handoff.py`、`docs/interfaces/elevator_field_evidence_trace_material_backfill_review_handoff.md`、本 sprint `tech-done.md` 中 Autonomy 小节 | 实现 PC-only material backfill review handoff gate、same-ref 校验、review decision contract 校验、owner handoff package、safe rerun hints、phone-safe copy、unsafe copy 阻断、focused unittest、interface docs |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/operator_gateway_diagnostics.md`、本 sprint `tech-done.md` 中 Robot 小节 | 新增 `robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary` safe alias，只读消费 summary，缺失/unsupported/unsafe/success claim fail closed |
| full-stack-software-engineer | `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中 Full-Stack 小节 | 新增 mobile/web 只读 material backfill review handoff panel，展示 owner handoff、safe rerun hints、phone-safe copy、missing/rejected materials 和 boundary；Start Delivery、Confirm Dropoff、Cancel gating 不变 |
| product-okr-owner | 实现完成后：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、本 sprint `side2side_check.md`、本 sprint `final.md` | 只按 worker 验证结果做 Product/OKR closeout；不得把 software-proof handoff 写成实机通过 |

## 5. 接口影响

- 新增 PC evidence artifact schema：`trashbot.elevator_field_evidence_trace_material_backfill_review_handoff.v1`。
- 新增 PC evidence summary schema：`trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1`。
- 新增 Robot diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary`。
- mobile/web 只读消费该 alias 或 fixture 字段。
- 不修改 `TrashCollection` action schema，不修改 `/cmd_vel`，不修改 serial/UART/hardware launch 参数，不修改 cloud relay command contract。
- 不新增硬件事实；若实现触及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸、2D LiDAR / ToF SKU 或 HIL-entry，worker 必须先读 `docs/vendor/VENDOR_INDEX.md` 并在代码注释、提交说明或最终说明中引用本地资料来源。

## 6. 子 Agent 执行要求

实现阶段主节点必须按 AGENTS 固定结构派发 worker，prompt 包含对应 `.codex/agents/<role>.toml` 的完整 System Prompt，并明确“你不是独自在代码库中工作，不要回滚或覆盖其他 worker / 用户改动”。

本 sprint 不允许 Product 在 implementation 前创建 `tech-done.md`、`side2side_check.md`、`final.md` 或更新 `OKR.md`。只有 worker 返回实际改动和验证证据后，Product 才能收口。

## 7. 验收命令

### Product planning gate

```bash
test -f sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/pre_start.md && test -f sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/prd.md && test -f sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|elevator_field_evidence_trace_material_backfill_review_handoff|Objective 5|Objective 1|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|autonomy-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
git diff --check -- sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
```

### Autonomy worker

```bash
python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_handoff.py
python3 -m unittest tests/test_elevator_field_evidence_trace_material_backfill_review_handoff.py
rg -n "elevator_field_evidence_trace_material_backfill_review_handoff|elevator_field_evidence_trace_material_backfill_review_decision|safe_evidence_ref|same_evidence_ref_required|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_field_owner_material_backfill_rerun_not_proven|needs_field_owner_material_handoff_not_proven|safe_rerun_hints|phone_safe_copy" pc-tools/evidence tests docs/interfaces/elevator_field_evidence_trace_material_backfill_review_handoff.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
git diff --check -- pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_handoff.py tests/test_elevator_field_evidence_trace_material_backfill_review_handoff.py docs/interfaces/elevator_field_evidence_trace_material_backfill_review_handoff.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
```

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary|elevator_field_evidence_trace_material_backfill_review_handoff|elevator_field_evidence_trace_material_backfill_review_decision|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_field_owner_material_backfill_rerun_not_proven|needs_field_owner_material_handoff_not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_field_evidence_trace_material_backfill_review_handoff|robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary|elevator_field_evidence_trace_material_backfill_review_decision|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_rerun_hints|phone_safe_copy|field_owner_handoff" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff
```

## 8. 风险边界

- 本 sprint planning 不修改产品代码、测试代码、硬件配置、`OKR.md` 或 `docs/process/okr_progress_log.md`。
- 后续 implementation 即使通过全部验收，也只能算 Docker/local `software_proof`。
- `ready_for_field_owner_material_backfill_rerun_not_proven` 只表示 handoff package 安全且齐全到可交给现场 owner 补材料并 rerun，不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、dropoff/cancel completion、delivery success、真实 phone/browser、WAVE ROVER/UART/HIL、PR #5 真实 2D LiDAR / ToF 材料或 Objective 5 external proof。
- operator material refs 必须只以安全摘要进入 Robot/mobile；不得暴露 raw JSON、原始本机路径、credentials、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、checksum、完整 artifact 或 traceback。
- safe rerun hints 只能描述材料补齐和 review rerun，不得触发 ACK、cursor、Start Delivery、Confirm Dropoff、Cancel 或任何 robot command。

## 9. 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时创建 `side2side_check.md` 和 `final.md`，并按实际结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- OKR closeout 只能记录 material backfill review handoff 的 `software_proof` 可执行交接；不得提高 Objective 5 external proof、Objective 1 HIL/hardware pass，也不得把 Objective 2 / Objective 3 写成真实 field pass。
