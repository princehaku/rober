# Sprint 2026.05.17_10-11 Route Task Field Retest Callback Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

### Task A - Autonomy

Owner：`autonomy-engineer`

实际改动文件：

- `pc-tools/evidence/route_task_field_retest_callback_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_callback_review_decision.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实际完成：

- 新增 dependency-free CLI：`--callback-intake-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 兼容 callback intake artifact、summary、wrapper 和 nested JSON。
- 输出 `trashbot.route_task_field_retest_callback_review_decision.v1` 与 `trashbot.route_task_field_retest_callback_review_decision_summary.v1`。
- Review decision 覆盖 `ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema`、`blocked_unsafe_callback`、`blocked_success_claim`。
- 持续保持 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### Task B - Robot

Owner：`robot-software-engineer`

实际改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实际完成：

- 新增 `route_task_field_retest_callback_review_decision` / `_summary` metadata-only diagnostics consumer。
- 支持 artifact、summary wrapper、Robot-compatible summary 和 nested diagnostics summary。
- 只暴露 safe summary、safe `evidence_ref`、review decision、source intake status、blocked reasons、next required evidence、result-intake readiness、owner handoff、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 对 missing、unsupported、unsafe、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。

### Task C - Full-stack

Owner：`full-stack-software-engineer`

实际改动文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实际完成：

- mobile/web 新增只读“现场回执复核决策” panel。
- 消费 `route_task_field_retest_callback_review_decision`、`route_task_field_retest_callback_review_decision_summary` 和 `robot_diagnostics_route_task_field_retest_callback_review_decision_summary`。
- 展示 review decision、safe `evidence_ref`、source intake status、缺失/回填摘要、result-intake readiness、owner handoff。
- copy/export whitelist-only；未新增 Start、Confirm、Cancel、ACK、cursor、robot command 或 result-intake 请求；主操作 gating 未改变。

### Task D - Product Closeout

Owner：`product-okr-owner`

实际改动文件：

- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/tech-done.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/side2side_check.md`
- `sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实际完成：

- 汇总 A/B/C worker 证据和失败定位。
- 按 Docker-only software proof boundary 收口，明确本轮不是 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof、真实投放、dropoff/cancel completion 或 delivery success。
- 保守更新 OKR：Objective 2 / Objective 3 从约 90% 到约 91%；Objective 4 保持约 99%；Objective 5 保持约 68%；Objective 1 保持约 77%。
- 将本 sprint 进度追加到 `docs/process/okr_progress_log.md`。

## 2. 验证结果

### Task A 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_callback_review_decision.py`：passed。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_callback_review_decision.py`：`Ran 5 tests in 0.029s OK`。
- `python3 pc-tools/evidence/route_task_field_retest_callback_review_decision.py --help`：passed。
- Required `rg`：passed。
- Scoped `git diff --check`：passed。
- 新增文件 no-index whitespace check：passed。

### Task B 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：passed。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 142 tests in 0.207s OK`。
- Required `rg`：passed。
- Scoped `git diff --check`：passed。

### Task C 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 38 tests OK`。
- `node --check mobile/web/app.js`：exit 0。
- Required `rg`：passed。
- Scoped `git diff --check`：passed。

### Task D 验证

- `rg -n "route_task_field_retest_callback_review_decision|software_proof_docker_route_task_field_retest_callback_review_decision_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision OKR.md docs/process/okr_progress_log.md`：passed。
- `git diff --check -- sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/tech-done.md sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/side2side_check.md sprints/2026.05.17_10-11_route-task-field-retest-callback-review-decision/final.md OKR.md docs/process/okr_progress_log.md`：passed。

## 3. 失败定位

- Task A 首轮失败：`blocked_success_claim` 修复提示中的 “delivery success” 触发最终安全防线，被误降级为 `blocked_unsafe_callback`。
- 修复方式：收窄最终安全防线，让决策枚举和 fail-closed 修复提示可以表达被阻断的成功声明，而不把自身安全提示误判为 unsafe callback。
- 复验结果：Task A py_compile、unittest、CLI help、required `rg`、scoped diff check 和 no-index whitespace check 均通过。
- Task B / Task C / Task D 本轮未报告未修复验证失败。

## 4. 剩余风险

- 本轮仍是 Docker-only software proof，不是真实 route/elevator field pass。
- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和同一 `evidence_ref` 的上车实机复账。
- 仍缺真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`。
- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof，因此本轮不提升。
- PR #5 暴露的 2D LiDAR / ToF、vendor/source、receipt、procurement、installation、wiring、power、calibration 和 HIL-entry 仍是独立缺口。
