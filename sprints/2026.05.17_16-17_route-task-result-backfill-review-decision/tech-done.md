# Sprint 2026.05.17_16-17 Route Task Result Backfill Review Decision - Tech Done

sprint_type: epic

## 1. 当前结论

状态：`DONE_SOFTWARE_PROOF_DOCKER_ONLY`。

Product closeout 于 2026-05-17 16:20 Asia/Shanghai 复核工作区时，A/B/C 工程交付均已落地。当前 sprint 已完成 `route_task_field_retest_result_backfill_review_decision` PC gate、Robot diagnostics metadata-only consumer 和 mobile/web 只读 panel。

本轮证据边界固定为 `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`。所有 closeout 均保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不证明真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 2. 用户价值和产品北极星

用户价值：把上一轮 route/elevator result backfill 从“材料入口”推进到“复核决策”，让现场支持人员和普通手机用户能看懂 accepted / missing / rejected material status、owner handoff、next required evidence 和 rerun commands。

产品北极星：服务低成本 ROS2 垃圾投递机器人闭环，让送垃圾、电梯 assisted delivery、现场材料补录和失败复盘形成可追溯证据链；本轮目标是 review decision surface，不是真实送达，也不是 O5 external proof。

## 3. OKR 映射

- Objective 2：完成 route/elevator task result backfill review decision，补齐 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 的 accepted / missing / rejected 复核决策层。Objective 2 从约 96% 保守更新到约 97%。
- Objective 3：完成 Nav2/fixed-route runtime log、route completion signal、task record 与同一 `evidence_ref` 的 material status、owner handoff、next required evidence、rerun commands 复核层。Objective 3 从约 96% 保守更新到约 97%。
- Objective 4：mobile/web 新增只读“路线任务回填复核决策” panel，但无真实手机设备、production app 或真实 PWA prompt/user choice 证据，因此保持约 99%。
- Objective 5：仍约 68%，是数值最低 Objective，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本轮不推进 O5，也不把 Docker-only metadata 写成 production proof。

## 4. KR 拆解和本轮核心抓手

核心抓手：`route_task_field_retest_result_backfill_review_decision` 决策层。

- KR-A Autonomy：完成 PC gate，输出 `trashbot.route_task_field_retest_result_backfill_review_decision.v1` artifact / summary，包含 `accepted_materials`、`missing_materials`、`rejected_materials`、`owner_handoff`、`next_required_evidence` 和 `rerun_commands`。
- KR-B Robot：完成 diagnostics metadata-only consumer，支持 explicit file/env/top-level/nested summary，fail closed，保持 task_orchestrator/action/Start/Dropoff/Cancel/ACK/cursor/Nav2/HIL 控制语义不变。
- KR-C Full-stack：完成 mobile/web 只读“路线任务回填复核决策” panel，copy/export 由 `safe_copy` 授权，缺失显示 `blocked copy unavailable`，Start / Confirm Dropoff / Cancel gating 不变。
- KR-D Product：完成 sprint closeout、OKR 更新和 progress log 更新，并保持 evidence boundary。

## 5. 实际改动

Task A / Autonomy：

- `pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_result_backfill_review_decision.py`
- `docs/interfaces/evidence_contracts.md`

Task B / Robot：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C / Full-stack：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task D / Product closeout：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/tech-done.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/side2side_check.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/final.md`

## 6. 验收结果

Task A / Autonomy：

- py_compile pass。
- focused unittest `Ran 5 tests ... OK`。
- CLI `--help` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- 实现支持 `trashbot.route_task_field_retest_result_acceptance_backfill.v1` / `_summary.v1`，输出 `trashbot.route_task_field_retest_result_backfill_review_decision.v1` / `_summary.v1`。
- fail closed 覆盖 bad/missing JSON、unsupported schema/boundary、backfill not ready、evidence_ref mismatch、weak `same_evidence_ref_required`、unsafe copy、success/control claim、`delivery_success=true`、`primary_actions_enabled=true`。

Task B / Robot：

- py_compile pass。
- diagnostics unittest `Ran 150 tests in 0.232s OK`。
- required `rg` pass。
- scoped `git diff --check` pass。
- diagnostics metadata-only consumer `route_task_field_retest_result_backfill_review_decision` / `_summary` 已落地。

Task C / Full-stack：

- mobile unittest `Ran 46 tests in 0.163s OK`。
- `node --check mobile/web/app.js` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- mobile/web 只读 panel 已落地，copy/export 由 `safe_copy` 授权，缺失显示 `blocked copy unavailable`。

Task D / Product：

- closeout required `rg` pass。
- closeout scoped `git diff --check` pass。

## 7. 剩余风险和证据链缺口

- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result、delivery success、真实手机/browser、WAVE ROVER、UART、HIL 和 O5 external proof。
- PR #4 elevator-assisted delivery 主线已从 backfill 入口推进到 review decision，但仍需真实现场材料回填。
- PR #5 hardware materials 仍缺真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定和 HIL-entry，不应继续包装。
- Objective 5 仍最低，但缺真实 external proof，本轮不提升。
