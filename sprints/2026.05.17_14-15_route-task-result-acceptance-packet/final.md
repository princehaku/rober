# Sprint 2026.05.17_14-15 Route Task Result Acceptance Packet - Final

sprint_type: epic

## 1. 最终结论

本轮完成 `route_task_field_retest_result_acceptance_packet` acceptance packet chain。PC gate、Robot diagnostics 和 mobile/web 三侧均能只读处理结果验收包，并保持 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

这推进了 PR #4 route/elevator evidence chain 的可执行性：上一轮 result reconciliation 已能复账 lineage，本轮进一步把八类 result materials、缺口、owner handoff、rerun commands 和 pass/fail criteria 转成现场复测验收包。该结果不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery result、HIL、真实手机/browser、Objective 5 external proof 或 PR #5 真实硬件材料。

## 2. 实际改动

- Autonomy：新增 PC gate `route_task_field_retest_result_acceptance_packet` 与 focused unittest，更新 `pc-tools/README.md` 和 `docs/navigation/fixed_route_workflow.md`。
- Robot：新增 acceptance packet diagnostics metadata-only consumer 和 diagnostics 单测，更新 `docs/interfaces/ros_contracts.md`。
- Full-stack：新增 mobile/web 只读“路线任务结果验收包” panel、fixture 和测试，更新 `docs/product/mobile_user_flow.md`。
- Product：更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md` 和本 `final.md`。

## 3. 验证结果

Task A / Autonomy：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py`：`Ran 5 tests in 0.052s OK`。
- `python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py --help`：pass。
- Required `rg` 和 scoped `git diff --check`：pass。

Task B / Robot：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 146 tests in 0.219s OK`。
- Required `rg` 和 scoped `git diff --check`：pass。

Task C / Full-stack：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：`Ran 42 tests OK`。
- `node --check mobile/web/app.js`：pass。
- Required `rg` 和 scoped `git diff --check`：pass。

Task D / Product：

- Required `rg` 命中 `route_task_field_retest_result_acceptance_packet`、`route_task_field_retest_result_reconciliation`、Objective 2 / 3 / 5、PR #4 / PR #5、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet`：pass。

## 4. OKR 进度更新

- Objective 2：约 94% -> 约 95%。理由：PR #4 route/elevator result materials 现在可从 result reconciliation 转成 acceptance packet，现场复测所需 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 可按同一 `evidence_ref` 执行验收。
- Objective 3：约 94% -> 约 95%。理由：Nav2/fixed-route runtime log、route completion signal、task record 等 result materials 现在具备 PC / Robot / mobile 三侧只读 acceptance packet、rerun commands 和 pass/fail criteria。
- Objective 1：保持约 77%。没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 4：保持约 99%。虽然 mobile/web 新增只读 panel，但没有真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 或真实现场 phone behavior。
- Objective 5：保持约 68%。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他真实 external proof。

## 5. OKR 最低优先级核对回顾

`OKR.md` 4.1 当前数值最低仍是 Objective 5（约 68%）。本 sprint 未针对 Objective 5，理由仍成立：本机 Docker-only，缺真实 external proof。继续把 `route_task_field_retest_result_acceptance_packet` 或其他 local metadata summary 写成 O5 production proof，会违反 `OKR.md` 第 6 节 stop rule。

本轮针对 Objective 2 / Objective 3 是合理的：PR #4 route/elevator evidence chain 已通过 handoff、result-intake、result-reconciliation 走到 acceptance packet，可执行缺口是把下一次现场复测的材料、重跑和 pass/fail criteria 固化下来。

PR #5 hardware blocker 仍成立：没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料，本轮不得把硬件缺口包装成已完成。

## 6. 剩余风险和下一步

下一步若继续推进 O2/O3，应补真实现场材料并回填同一 `evidence_ref`：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。

若要推进 Objective 5，必须先拿到至少一种真实 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。若要解除 PR #5，必须补真实 2D LiDAR / ToF 采购、安装、接线、供电、标定和 HIL-entry 材料。
