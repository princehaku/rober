# Sprint 2026.05.19_02-03 Elevator Feedback Task Record Trace - Tech Plan

## OKR 最低优先级核对

1. Live `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。理由：本机是 Docker-only，仍缺真实 HTTPS/TLS、公网 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和 real phone/browser external proof；继续本地 O5 wrapper 不能推进 O5 completion。
3. 次低 Objective 1 约 81%，本 sprint 也不针对 Objective 1。理由：当前仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 暴露的 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍是独立缺口。本机没有真实硬件，不消费同一 blocker。
4. 本 sprint 针对 Objective 2 / Objective 4。PR #4 已把 elevator assisted delivery 拉入必达主链；最近两轮已完成 `current_step=elevator:<phase>` 的 Robot 实时 feedback 和 mobile/web 只读展示。最新可行动缺口是 post-run task_record、diagnostics、mobile trace 在 same `evidence_ref` 下对齐。

## 技术目标

把 `TrashCollection.Feedback.current_step=elevator:<phase>` 从实时展示推进到 post-run trace：

- Robot task_record 或等价 post-run artifact 记录 elevator phase timeline。
- Operator diagnostics 暴露 metadata-only safe summary。
- Mobile/web 展示上一轮电梯阶段复盘。
- 三者通过同一 safe `evidence_ref` 对齐，全部保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 接口契约草案

建议 Robot worker 采用兼容性优先的 summary 结构，实际字段名可按现有代码风格调整，但语义不得放宽：

```json
{
  "schema": "trashbot.elevator_feedback_task_record_trace_summary.v1",
  "source": "software_proof",
  "evidence_ref": "safe-field-owner-ref",
  "trace_status": "software_trace_ready",
  "phase_trace": [
    {
      "current_step": "elevator:waiting_elevator_open",
      "observed_from": "action_feedback",
      "recorded_in_task_record": true
    }
  ],
  "task_record_ref": "sanitized-task-record-ref",
  "diagnostics_summary": {
    "missing_real_materials": [
      "real_elevator_door_state",
      "real_floor_confirmation",
      "real_nav2_or_fixed_route_runtime_log",
      "real_dropoff_or_cancel_completion"
    ]
  },
  "not_proven": [
    "real_elevator",
    "real_phone_browser_external_proof",
    "real_nav2_fixed_route",
    "hil_pass",
    "delivery_success"
  ],
  "delivery_success": false,
  "primary_actions_enabled": false
}
```

约束：

- `current_step` 必须匹配 `elevator:<phase>` 的白名单；unknown/missing/non-elevator fail closed。
- `evidence_ref` 必须 safe，并与 task_record、diagnostics、mobile fixture 一致。
- diagnostics / mobile 只能消费 summary，不读取完整 raw artifact、raw ROS topic、串口、凭证、本机路径或 traceback。
- `delivery_success=false` 和 `primary_actions_enabled=false` 必须是布尔 false，不能是字符串。

## 文件范围和 owner 分工

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/**`、相关 Robot tests、`docs/interfaces/**`、`docs/product/elevator_assisted_delivery.md`、本 sprint `tech-done.md` 中自己的小节 | 生成/汇总 elevator post-run trace，接入 diagnostics safe summary，补 focused tests 和接口文档 |
| full-stack-software-engineer | `mobile/web/**`、`mobile/fixtures/**`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中自己的小节 | 只读展示 post-run elevator trace，补 fixture 和前端验证 |
| hardware-engineer | 只读 `docs/vendor/VENDOR_INDEX.md`、PR #5 相关硬件文档；如必须写，只能在 `tech-done.md` 记录只读核对结论 | 核对 PR #5 2D LiDAR / ToF 材料缺口仍独立，不改硬件配置 |
| product-okr-owner | `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `side2side_check.md` / `final.md`（实现完成后） | 验收边界和 OKR 收口；本规划阶段只写三份 planning docs |

Robot 和 Full-Stack 文件范围互不重叠，进入实现时必须并行启动两个 worker；Hardware 可作为只读事实核对 worker，与实现并行。

## 验收命令

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "elevator_feedback_task_record_trace|current_step=elevator:<phase>|task_record|diagnostics|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces docs/product/elevator_assisted_delivery.md sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces docs/product/elevator_assisted_delivery.md sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_feedback_task_record_trace|current_step=elevator:<phase>|task_record|diagnostics|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
```

### Hardware fact-check worker

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "2D LiDAR|ToF|PR #5|vendor|source|HIL-entry|software_proof|not_proven" docs/vendor docs/product docs/interfaces sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
```

### Product planning gate

```bash
test -f sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/pre_start.md && test -f sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/prd.md && test -f sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|current_step=elevator:<phase>|task_record|diagnostics|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
git diff --check -- sprints/2026.05.19_02-03_elevator-feedback-task-record-trace
```

## 风险和 fail-closed 规则

- 不得把 trace summary 写成真实电梯、真实送达、真实 Nav2/fixed-route、真实手机/browser、O5 external proof、WAVE ROVER/UART/HIL 或 PR #5 hardware proof。
- 不得用 trace summary 启用 Start Delivery、Confirm Dropoff、Cancel，或生成 ACK/cursor/command。
- 不得暴露 raw JSON artifact、本机绝对路径、ROS topic、`/cmd_vel`、串口设备、波特率、WAVE ROVER 参数、凭证、traceback 或完整内部日志。
- 如果 `evidence_ref` 缺失、不安全或不一致，diagnostics 和 mobile 必须显示缺失/不可复盘，而不是补默认成功值。
- 如果 task_record 里没有 elevator phase timeline，summary 必须标记 missing trace，不得从手机实时展示反推 task_record 已落盘。

## 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时再创建 `side2side_check.md` 和 `final.md`，并按实际结果决定是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 若只完成 planning，不得更新 OKR 百分比；本阶段不生成 `tech-done.md`、`side2side_check.md`、`final.md`。
