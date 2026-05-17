# Sprint 2026.05.17_17-18 Route Task Result Review Dispatch - Tech Done

sprint_type: epic

## 1. 当前结论

状态：`DONE_SOFTWARE_PROOF_DOCKER_ONLY`。

Product closeout 于 2026-05-17 17:20 Asia/Shanghai 复核工作区时，A/B/C 工程交付均已落地。当前 sprint 已完成 `route_task_field_retest_result_review_dispatch` PC gate、Robot diagnostics metadata-only consumer 和 mobile/web 只读 panel。

本轮证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_dispatch_gate`。所有 closeout 均保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不证明真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 2. 用户价值和产品北极星

用户价值：把上一轮 route/elevator result backfill review decision 从“复核决策”推进到“现场派发”，让现场支持人员能直接看到 accepted / missing / rejected material categories、owner work orders、callback packet requirements 和 rerun commands。

产品北极星：服务低成本 ROS2 垃圾投递机器人闭环，让送垃圾、电梯 assisted delivery、现场材料补录和失败复盘形成可追溯证据链；本轮目标是 review dispatch surface，不是真实送达，也不是 O5 external proof。

## 3. OKR 映射

- Objective 2：完成 route/elevator task result review dispatch，补齐 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 的 owner work orders、callback packet requirements 和 rerun commands。Objective 2 从约 97% 保守更新到约 98%。
- Objective 3：完成 Nav2/fixed-route runtime log、route completion signal、task record 与同一 `evidence_ref` 的派发状态、复跑命令和回调包要求。Objective 3 从约 97% 保守更新到约 98%。
- Objective 4：mobile/web 新增只读“路线任务现场派发” panel，但无真实手机设备、production app 或真实 PWA prompt/user choice 证据，因此保持约 99%。
- Objective 5：仍约 68%，是数值最低 Objective，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本轮不推进 O5，也不把 Docker-only metadata 写成 production proof。

## 4. KR 拆解和本轮核心抓手

核心抓手：`route_task_field_retest_result_review_dispatch` 派发层。

- KR-A Autonomy：完成 PC gate，输出 `trashbot.route_task_field_retest_result_review_dispatch.v1` artifact / summary，包含 `accepted_materials`、`missing_materials`、`rejected_materials`、`owner_work_orders`、`callback_packet_requirements` 和 `rerun_commands`。
- KR-B Robot：完成 diagnostics metadata-only consumer，支持 file/env/top-level/nested summary，fail closed，保持 task_orchestrator/action/Start/Dropoff/Cancel/ACK/cursor/Nav2/HIL 控制语义不变。
- KR-C Full-stack：完成 mobile/web 只读“路线任务现场派发” panel，copy/export 由 `safe_copy` 白名单授权，缺失显示 `blocked copy unavailable`，Start / Confirm Dropoff / Cancel gating 不变。
- KR-D Product：完成 sprint closeout、OKR 更新和 progress log 更新，并保持 evidence boundary。

## 5. 实际改动

Task A / Autonomy：

- `pc-tools/evidence/route_task_field_retest_result_review_dispatch.py`
- `pc-tools/evidence/test_route_task_field_retest_result_review_dispatch.py`
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
- `sprints/2026.05.17_17-18_route-task-result-review-dispatch/tech-done.md`
- `sprints/2026.05.17_17-18_route-task-result-review-dispatch/side2side_check.md`
- `sprints/2026.05.17_17-18_route-task-result-review-dispatch/final.md`

## 6. 验收结果

Task A / Autonomy：

- py_compile pass。
- focused unittest `Ran 5 tests in 0.061s OK`。
- CLI `--help` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- 实现支持 `trashbot.route_task_field_retest_result_backfill_review_decision.v1` / `_summary.v1`，输出 `trashbot.route_task_field_retest_result_review_dispatch.v1` / `_summary.v1`。
- fail closed 覆盖 bad/missing JSON、unsupported schema/boundary、review decision not ready、evidence_ref mismatch、unsafe copy、success/control claim、`delivery_success=true`、`primary_actions_enabled=true`。

Task B / Robot：

- py_compile pass。
- diagnostics unittest `Ran 152 tests ... OK`。
- required `rg` pass。
- scoped `git diff --check` pass。
- diagnostics metadata-only consumer `route_task_field_retest_result_review_dispatch` / `_summary` 已落地。
- 初次失败为 nested summary 覆盖 top-level 导致 safe_evidence_ref missing，已修复并复验。

Task C / Full-stack：

- mobile unittest `Ran 48 tests in 0.171s OK`。
- `node --check mobile/web/app.js` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- mobile/web 只读 panel 已落地，copy/export 由 `safe_copy` 白名单授权，缺失显示 `blocked copy unavailable`。
- 初次 fixture 文案含 raw path material，已改为 phone-safe `unsafe material reference` 并复验。

Task D / Product：

- closeout required `rg` pass。
- closeout scoped `git diff --check` pass。

## 7. 剩余风险和证据链缺口

- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result、delivery success、真实手机/browser、WAVE ROVER、UART、HIL 和 O5 external proof。
- PR #4 elevator-assisted delivery 主线已从 backfill review decision 推进到 review dispatch，但仍需真实现场材料回填。
- PR #5 hardware materials 仍缺真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定和 HIL-entry，不应继续包装。
- Objective 5 仍最低，但缺真实 external proof，本轮不提升。
