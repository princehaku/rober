# Sprint 2026.05.16_22-23 Route Task Field Retest Result Intake - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_result_intake_gate`。目标是把上一轮 `route_task_field_retest_session_handoff` 之后的现场复测结果材料，转成 PC result intake artifact / summary、Robot diagnostics metadata-only consumer、mobile/web 只读 panel 和 Product closeout 记录。

统一边界保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不证明真实 field pass、真实 Nav2/fixed-route、真实电梯、真实投放、真实取消完成、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。

### Task A Autonomy

改动文件：

- `pc-tools/evidence/route_task_field_retest_result_intake.py`
- `pc-tools/evidence/test_route_task_field_retest_result_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

完成内容：

- 新增 `trashbot.route_task_field_retest_result_intake.v1` 与 `trashbot.route_task_field_retest_result_intake_summary.v1` PC gate。
- 支持 result artifact、summary、wrapper、nested JSON 输入。
- 检查八类结果材料摘要：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。
- 输出 `material_completeness`、`missing_materials`、`operator_next_steps`、`field_callback_checklist`、`rerun_summary`、`fail_closed_phone_safe_summary`。
- 已修复初版问题：`required_result_materials` 被误当成已回填材料，普通绝对路径未脱敏。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_intake.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_intake.py
Ran 8 tests in 0.036s
OK

python3 pc-tools/evidence/route_task_field_retest_result_intake.py --help
pass

required rg
pass

git diff --check -- pc-tools/evidence/route_task_field_retest_result_intake.py pc-tools/evidence/test_route_task_field_retest_result_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
pass
```

失败定位：首轮发现 `required_result_materials` 与普通绝对路径脱敏问题，Autonomy worker 已修复并复验通过。

### Task B Robot

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

完成内容：

- 新增 `route_task_field_retest_result_intake` / `_summary` diagnostics consumer。
- 支持 direct artifact、summary wrapper、env vars、top-level status、nested diagnostics summary。
- 只输出 metadata-only phone-safe summary，不改变 task_orchestrator、collect/dropoff/cancel、ACK、Nav2、HIL 或 delivery success 语义。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `software_proof_docker_route_task_field_retest_result_intake_gate`。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 116 tests in 0.143s
OK

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
pass
```

失败定位：未报告未修复失败。

### Task C Full-stack

改动文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

完成内容：

- 新增“路线任务现场复测结果入口”只读 panel。
- 消费 result intake summary 与 Robot diagnostics compatible summary。
- 展示 intake status、safe `evidence_ref`、material completeness、八类材料摘要、missing material list、operator next steps、safe copy 状态、`not_proven`、false action flags 和 evidence boundary。
- copy/export whitelist-only；Start / Confirm Dropoff / Cancel 授权未改。
- 在允许范围内修复既有 `nextEvidence` fallback guard。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 18 tests in 0.033s
OK

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
pass

fixture-backed DOM check
pass
```

失败定位：截图捕获超时，但 fixture-backed DOM 检查和按钮状态检查完成；未把截图超时写成浏览器 proof。

## 2. Product closeout

Product closeout 更新：

- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/tech-done.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/side2side_check.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

OKR 保守判断：

- Objective 1 保持约 75%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 2 从约 82% 保守上调到约 83%。理由是 result intake 已把真实 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 的回填入口变成可检查合同；不是 field pass。
- Objective 3 从约 82% 保守上调到约 83%。理由是 result intake 已把真实 Nav2/fixed-route runtime log、route completion signal、task record 和 rerun summary 变成可对账入口；不是真实 Nav2/fixed-route 实跑。
- Objective 4 从约 91% 保守上调到约 92%。理由是 mobile/web 能 phone-safe 展示 result intake 状态和缺口，且 copy/export fail closed、主操作授权不变；不是真实手机/browser 或 production app proof。
- Objective 5 保持约 66%。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或外部云材料。

## 3. 验证范围

Product closeout 运行：

```text
rg -n "route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_22-23_route-task-field-retest-result-intake
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_22-23_route-task-field-retest-result-intake/tech-done.md sprints/2026.05.16_22-23_route-task-field-retest-result-intake/side2side_check.md sprints/2026.05.16_22-23_route-task-field-retest-result-intake/final.md
pass
```

## 4. 剩余风险

- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion 和 delivery_result。
- 仍缺真实电梯、真实路线采集、真实 WAVE ROVER/UART/HIL、真实手机/browser、production app 和真实 Objective 5 external proof。
- PR #4 已要求 elevator-assisted delivery 是主线必须能力；本轮只补结果 intake readiness，还没有实景闭环。
- PR #5 硬件/source/config blocker 已被 `17-18_hardware-baseline-source-alignment` 与 `18-19_hardware-sensor-hil-entry-config-precheck` 连续两轮消费；本轮没有第三次消费该 blocker。
