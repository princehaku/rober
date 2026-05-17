# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - Tech Done

sprint_type: epic

## 1. 实际改动

A / Autonomy worker 完成 `software_proof_docker_route_task_field_retest_operator_drill_gate` 的 review-decision input upgrade：

- 修改 `pc-tools/evidence/route_task_field_retest_operator_drill.py`，让 operator drill 优先消费 `route_task_field_retest_material_callback_review_decision` artifact / summary / wrapper / nested diagnostics。
- 保留 material pack 兼容；mixed wrapper 中优先 review decision，避免回退到 material pack-only drill。
- 修改 `pc-tools/evidence/test_route_task_field_retest_operator_drill.py`，覆盖 review decision artifact / summary / wrapper / nested diagnostics、mixed wrapper 优先级和 fail-closed 边界。
- 更新 `docs/interfaces/evidence_contracts.md`，说明 `route_task_field_retest_operator_drill` 可承接 `route_task_field_retest_material_callback_review_decision`，但仍不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

B / Robot worker 完成 diagnostics 只读承接：

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，新增 `robot_diagnostics_route_task_field_retest_operator_drill_summary` output alias。
- 支持 nested/top-level discovery，并对 review-decision-derived raw fields 做 fail-closed whitelist filtering。
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`，覆盖新 alias、nested/top-level discovery 和 raw field 过滤。
- 更新 `docs/interfaces/ros_contracts.md`，保持 diagnostics metadata-only，不启用 task_orchestrator、Start、Confirm Dropoff、Cancel、ACK、Nav2、HIL 或 primary actions。

C / Full-stack worker 完成手机首屏只读承接：

- 修改 `mobile/web/app.js`，让“现场操作演练”承接 material callback review decision，展示 source decision、operator drill status、safe `evidence_ref`、commands、checklist、outputs、rerun 和 boundary。
- 修改 `mobile/fixtures/mobile_web_status.fixture.json` 与 `mobile/web/test_mobile_web_entrypoint.py`，覆盖 first-screen panel、copy/export whitelist-only 和 fail-closed 文案。
- 更新 `docs/product/mobile_user_flow.md`，明确该 panel 不是真实手机/browser、真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL 或 O5 external proof。

Product closeout 仅更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/tech-done.md`
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/side2side_check.md`
- `sprints/2026.05.18_07-08_route-task-material-review-operator-drill/final.md`

## 2. 验证结果

A / Autonomy worker 报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_operator_drill.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_operator_drill.py
Ran 6 tests in 0.024s
OK

required rg
pass

git diff --check -- pc-tools/evidence/route_task_field_retest_operator_drill.py pc-tools/evidence/test_route_task_field_retest_operator_drill.py docs/interfaces/evidence_contracts.md
pass
```

B / Robot worker 报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 175 tests
OK

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
pass
```

C / Full-stack worker 报告：

```text
node --check mobile/web/app.js
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 72 tests
OK

required rg
pass

git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
pass
```

Product closeout 验收命令已执行：

```text
rg -n "route_task_field_retest_material_callback_review_decision|route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_07-08_route-task-material-review-operator-drill
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_07-08_route-task-material-review-operator-drill
pass
```

## 3. 偏差和失败定位

本轮 A/B/C worker 未报告功能验证失败。Product closeout 没有修改代码、测试、A/B/C docs 或硬件配置。

本轮没有运行完整 ROS2 Humble Docker colcon build，也没有运行真实手机设备/browser、真实 WAVE ROVER/UART/HIL、真实 Nav2/fixed-route 或真实 O5 external proof 验证；原因是本轮验收口径是 metadata-only software proof closeout，且本机没有真实硬件和外部云/4G/OSS/CDN/DB/queue 材料。

## 4. 剩余风险

本轮仍是 `software_proof_docker_route_task_field_retest_operator_drill_gate`，不是 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART、真实手机/browser 或 Objective 5 external proof。

Objective 5 保持约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和真实手机/browser external proof。

Objective 1 保持约 81%，仍缺真实 WAVE ROVER `hil_pass`、真实串口日志、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 实机样本、operator HIL report，以及 PR #5 相关 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

Objective 2 / 3 / 4 保守保持约 99%，下一步必须用 PR #4 真实 route/elevator field materials 或真实手机/browser/device 材料回填，不能把本轮 operator drill 写成现场通过。
