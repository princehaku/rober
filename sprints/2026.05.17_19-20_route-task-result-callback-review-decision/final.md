# Sprint 2026.05.17_19-20 Route Task Result Callback Review Decision - Final

sprint_type: epic

## 1. 最终结论

状态：`CLOSED_READY_FOR_INTEGRATION_COMMIT`。

本 sprint 完成 `route_task_field_retest_result_callback_review_decision`：承接上一轮 `route_task_field_retest_result_callback_intake`，把 callback packet 摄取结果转成可执行的复核决策、owner handoff、next required evidence 和 rerun path。A/B/C workers 均完成 scoped validation，Product closeout 已更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md` 和本 `final.md`。

证据边界：`software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`。本轮仍是 Docker-only / PC-only / metadata-only / read-only mobile software proof，不是真实 route/elevator field pass，不是真实手机/browser，不是 HIL，不是 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场支持能把 callback packet 的 accepted/missing/rejected updates 转成可复核的下一步决策，知道哪些材料可进入 result review、哪些需要 owner backfill、哪些需要 callback rerun 或 evidence-ref mismatch rerun。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“证据链可回填、可复核、可追责”，但每一步都不能越过真实硬件、真实路线、真实手机和真实外部云证据边界。

## 3. OKR 进度

- Objective 2：保持约 99%。理由是 PR #4 route/elevator callback updates 已能转成 review decision 和 owner handoff；仍不是真实送达。
- Objective 3：保持约 99%。理由是 Nav2/fixed-route runtime log、route completion signal、task record 等 result materials 的 accepted/missing/rejected 状态已有复核决策和复跑路径；仍不是真实路线实跑。
- Objective 4：保持约 99%。mobile/web 有只读 review-decision panel，但无真实 iPhone/Android、production app 或 PWA prompt/user choice。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：保持约 77%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 PR #5 真实 2D LiDAR / ToF 材料。

## 4. 实际改动文件

Product closeout 本轮改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-done.md`
- `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/side2side_check.md`
- `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md`

A/B/C workers 已完成的 durable work：

- `pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py`
- `docs/interfaces/evidence_contracts.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

## 5. 验证摘要

Task A / Autonomy：

- py_compile pass。
- unittest `Ran 6 tests OK`。
- CLI `--help` pass。
- required `rg` pass。
- scoped `git diff --check` pass。

Task B / Robot：

- py_compile pass。
- diagnostics unittest `Ran 156 tests OK`。
- required `rg` pass。
- scoped `git diff --check` pass。

Task C / Full-stack：

- mobile unittest `Ran 52 tests OK`。
- `node --check mobile/web/app.js` pass。
- required `rg` pass。
- scoped `git diff --check` pass。

Task D / Product：

- required closeout `rg` pass。
- Product scoped `git diff --check` pass。
- `tech-done.md`、`side2side_check.md`、`final.md` 文件存在。

## 6. OKR 最低优先级回顾

当前数值最低 Objective 仍是 Objective 5，约 68%。本 sprint 没有针对 Objective 5，因为继续提升 O5 必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/cutover 或真实手机/browser external proof。当前本机只有 Docker，A/B/C durable work 也全部属于 O2/O3 route/elevator callback-review-decision chain，因此没有移动 Objective 5。

这个理由在 final 收口时仍成立。

## 7. 剩余风险和下一步

- 需要真实现场 callback packet、review decision 后的材料回填和同一 `evidence_ref` 上车复账。
- 需要真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- 需要真实手机设备 / iPhone / Android / production app / PWA prompt/user choice 现场验收，才能继续证明 Objective 4 的设备侧口径。
- 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，才能继续推进 Objective 5。
- 需要 PR #5 的真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定与 HIL-entry 材料，才能推进相关硬件基线。
- 主会话后续应执行 final integration verifier，然后 commit/push；本 Task D 按要求不 commit。
