# Sprint 2026.05.17_15-16 Route Task Result Acceptance Backfill - Tech Done

sprint_type: epic

## 1. 实际改动

Task A / Autonomy 完成 PC 侧 `route_task_field_retest_result_acceptance_backfill` gate，新增 focused unittest。该 gate 接在 `route_task_field_retest_result_acceptance_packet` 后，输入 acceptance packet artifact / summary / wrapper 与 `--material-dir`，检查八类材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。输出 `trashbot.route_task_field_retest_result_acceptance_backfill.v1` / `_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task B / Robot 完成 diagnostics metadata-only consumer，更新 `operator_gateway_diagnostics.py`、diagnostics tests 和 `docs/interfaces/ros_contracts.md`。新增 `route_task_field_retest_result_acceptance_backfill` / `_summary` 只读消费路径，支持 file/env/top-level/nested summary，只暴露 safe backfill metadata，fail closed，未改变 task_orchestrator/action/Start/Dropoff/Cancel 控制语义。

Task C / Full-stack 完成 mobile/web 只读“路线任务结果回填” panel，更新 `mobile/web/app.js`、fixture、mobile tests 和 `docs/product/mobile_user_flow.md`。panel 展示 backfill status、source packet status、material completeness、same-evidence-ref alignment、missing/rejected categories、owner handoff、rerun commands、safe copy 和边界；copy/export 白名单，缺 safe_copy blocked，Start/Confirm Dropoff/Cancel gating 不变。

Task D / Product closeout 更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 `tech-done.md`、`side2side_check.md` 和 `final.md`。Objective 2 / Objective 3 因 PC / Robot / mobile 三侧 route/elevator acceptance backfill 入口从约 95% 保守更新到约 96%；Objective 5 仍最低但保持约 68%，因为仍缺真实 external proof。

## 2. 验证结果

Task A 验证：

```text
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_acceptance_backfill.py
Ran 5 tests ... OK

python3 pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py --help
PASS

required rg
PASS

scoped git diff --check
PASS
```

Task B 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 148 tests in 0.226s OK

required rg
PASS

scoped git diff --check
PASS
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 44 tests in 0.142s OK

node --check mobile/web/app.js
PASS

required rg
PASS

scoped git diff --check
PASS
```

Task D closeout 验证：

```text
rg -n "route_task_field_retest_result_acceptance_backfill|route_task_field_retest_result_acceptance_packet|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_15-16_route-task-result-acceptance-backfill
PASS

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_15-16_route-task-result-acceptance-backfill
PASS
```

## 3. 偏差和失败定位

本轮 Task D 未发现 closeout 验证失败。Task A / B / C 的实现验证均已由对应 worker 修复并复验通过。

## 4. 剩余风险

本轮证据边界是 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF 材料、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 production worker/migration/cutover。
