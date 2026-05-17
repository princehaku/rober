# Sprint 2026.05.18_05-06 Route Task Material Callback Packet - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_material_callback_packet_gate`，把上一轮 `route_task_field_retest_material_pack` 的 callback skeleton 推进为 PC / Robot / mobile 三面可消费的 callback packet。

Task A / Autonomy Algorithm Engineer 已完成：

- `pc-tools/evidence/route_task_field_retest_material_callback_packet.py`
- `pc-tools/evidence/test_route_task_field_retest_material_callback_packet.py`
- `docs/interfaces/evidence_contracts.md`

交付结果：

- 新增 PC-only dependency-free callback packet gate。
- 新增 artifact schema `trashbot.route_task_field_retest_material_callback_packet.v1`。
- 新增 summary schema `trashbot.route_task_field_retest_material_callback_packet_summary.v1`。
- 固定 evidence boundary `software_proof_docker_route_task_field_retest_material_callback_packet_gate`。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task B / Robot Platform Engineer 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

交付结果：

- 新增 Robot diagnostics metadata-only consumer。
- 输出 `route_task_field_retest_material_callback_packet`、`route_task_field_retest_material_callback_packet_summary`、`robot_diagnostics_route_task_field_retest_material_callback_packet_summary`。
- 保持只读 diagnostics，不触发 Start、Confirm Dropoff、Cancel、ACK、Nav2、HIL 或 primary actions。

Task C / User Touchpoint Full-Stack Engineer 已完成：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

交付结果：

- 新增只读“路线/电梯现场材料回执”panel。
- 从 status/readiness/diagnostics 多入口读取 callback packet summary。
- copy/export whitelist-only。
- Start Delivery、Confirm Dropoff、Cancel、dispatch、callback、robot command gating 保持不变。

Product closeout 已完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/tech-done.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/side2side_check.md`
- `sprints/2026.05.18_05-06_route-task-material-callback-packet/final.md`

## 2. 验证结果

Task A / Autonomy 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_callback_packet.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_callback_packet.py`：`Ran 5 tests OK`。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Task B / Robot 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 173 tests OK`。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Task C / Full-stack 验证：

- `node --check mobile/web/app.js`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：`Ran 70 tests OK`。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Product closeout 验证：

- `rg -n "route_task_field_retest_material_callback_packet|software_proof_docker_route_task_field_retest_material_callback_packet_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_05-06_route-task-material-callback-packet`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_05-06_route-task-material-callback-packet`
- 结果：required `rg` 覆盖 OKR、progress log 和本 sprint closeout 文档；scoped `git diff --check` exit 0。

## 3. OKR 进展

Objective 2 保持约 99%。本轮提升的是 route/elevator material callback packet 的可回填性、可复核性和 fail-closed 边界，不是真实 route/elevator field pass。

Objective 3 保持约 99%。本轮把 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result 的现场回执入口固化为 packet，但没有真实 Nav2/fixed-route 实跑或 task record/completion signal。

Objective 4 保持约 99%。本轮新增手机端只读“路线/电梯现场材料回执”panel，但没有真实手机/browser、production app 或真实 PWA prompt/user choice。

Objective 1 保持约 81%。本轮没有 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report、2D LiDAR / ToF SKU/source 或硬件事实。

Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。

## 4. 剩余风险

本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

PR #4 的真实现场材料仍待回填：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。

PR #5 的真实硬件材料仍待回填：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，以及 WAVE ROVER/UART/HIL 实机材料。
