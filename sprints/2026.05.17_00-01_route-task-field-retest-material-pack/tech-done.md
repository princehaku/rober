# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_material_pack` 四 owner 交付，证据边界统一保持为：

- `software_proof_docker_route_task_field_retest_material_pack_gate`
- `trashbot.route_task_field_retest_material_pack.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

Task A Autonomy 已完成：

- 修改 `pc-tools/evidence/route_task_field_retest_material_pack.py`
- 修改 `pc-tools/evidence/test_route_task_field_retest_material_pack.py`
- 修改 `pc-tools/README.md`
- 修改 `docs/navigation/fixed_route_workflow.md`

实际结果：

- 新增 dependency-free PC CLI，支持 `--material-dir`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 校验八类材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。
- 对同一 safe `evidence_ref`、缺失材料、placeholder-only、raw path、credential、unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true` 执行 fail-closed 或 rejected/missing。
- 输出 sanitized artifact 和 summary，fixture dry-run 保持 `ready_for_field_retest_material_pack_not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task B Robot 已完成：

- 修改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 修改 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 修改 `docs/interfaces/ros_contracts.md`

实际结果：

- 新增 `route_task_field_retest_material_pack` / `_summary` diagnostics metadata-only consumer。
- 对 missing、unsupported、mismatch、unsafe、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 只暴露 safe summary、material completeness、missing/rejected、same evidence ref、operator next steps 和 boundary。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success。

Task C Full-stack 已完成：

- 修改 `mobile/web/app.js`
- 修改 `mobile/web/styles.css`
- 修改 `mobile/web/test_mobile_web_entrypoint.py`
- 修改 `mobile/web/fixtures/status.json`
- 修改 `docs/product/mobile_user_flow.md`

实际结果：

- 新增只读“现场材料包” panel。
- 消费 material pack / summary / Robot diagnostics compatible summary。
- 展示 material completeness、same evidence ref、八类材料状态、missing/rejected、operator next steps、`not_proven` 和 boundary。
- Start Delivery、Confirm Dropoff、Cancel gating 未改变。

Task D Product Closeout 已完成：

- 新建本 `tech-done.md`
- 新建 `side2side_check.md`
- 新建 `final.md`
- 更新 `OKR.md`
- 更新 `docs/process/okr_progress_log.md`

## 2. 验证结果

Task A Autonomy 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_pack.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_pack.py
Ran 5 tests in 0.017s OK

python3 pc-tools/evidence/route_task_field_retest_material_pack.py --help
pass

required rg
pass

git diff --check -- pc-tools/evidence/route_task_field_retest_material_pack.py pc-tools/evidence/test_route_task_field_retest_material_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
pass

fixture dry-run
ready_for_field_retest_material_pack_not_proven; delivery_success=false; primary_actions_enabled=false
```

Task B Robot 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 120 tests in 0.160s OK

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
pass
```

Task C Full-stack 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 22 tests in 0.047s OK

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
pass
```

Task D Product Closeout 验证：

```text
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 2|Objective 3|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_00-01_route-task-field-retest-material-pack OKR.md docs/process/okr_progress_log.md
pass

git diff --check -- sprints/2026.05.17_00-01_route-task-field-retest-material-pack/tech-done.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/side2side_check.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/final.md OKR.md docs/process/okr_progress_log.md
pass
```

未运行 `git diff --cached --check`，因为本轮按要求没有 stage 任何文件。

## 3. 偏差

- 本轮没有真实现场材料目录，只通过 fixture / software proof 证明材料包 gate、diagnostics metadata-only consumer 和 mobile read-only panel。
- 本轮没有运行全量 ROS2 Docker/Humble build；验收范围按 tech-plan 围栏执行，为 targeted `py_compile`、focused unittest、`node --check`、required `rg` 和 scoped `git diff --check`。
- Product Closeout 未提交、未推送，符合本轮“不要提交、不要推送”的用户指令。

## 4. 剩余风险

- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 的同一 `evidence_ref` 现场材料目录。
- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL 和 Objective 5 external proof。
- Objective 5 仍约 66%，Docker-only 本地 material pack 不能替代真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
