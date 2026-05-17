# Sprint 2026.05.18_02-03 Route Task Result Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_result_review_decision`，承接上一轮 `route_task_field_retest_result_review_intake`，把 intake 的 missing materials、review-ready package、rerun package、safe `evidence_ref` 和 same-evidence-ref 要求转成明确复核决策。证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_decision_gate`。

Task A / Autonomy 已完成：

- 新增 `pc-tools/evidence/route_task_field_retest_result_review_decision.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_result_review_decision.py`。
- 更新 `docs/interfaces/evidence_contracts.md`。
- worker 报告 focused unittest `Ran 5 tests OK`。

Task B / Robot 已完成：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- worker 报告 diagnostics unittest `Ran 170 tests OK`。
- 输出 aliases：`route_task_field_retest_result_review_decision`、`route_task_field_retest_result_review_decision_summary`、`robot_diagnostics_route_task_field_retest_result_review_decision_summary`。

Task C / Full-stack 已完成：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- worker 报告 mobile unittest `Ran 66 tests OK`，`node --check mobile/web/app.js` pass。

Task D / Product closeout 本轮修改：

- `sprints/2026.05.18_02-03_route-task-result-review-decision/tech-done.md`
- `sprints/2026.05.18_02-03_route-task-result-review-decision/side2side_check.md`
- `sprints/2026.05.18_02-03_route-task-result-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 2. 用户价值和产品北极星

用户价值：支持同学拿到 result review intake 后，现在能看到明确的 review decision：可进入 result acceptance/backfill、缺材料需补、证据不一致需 rerun、或 schema / intake 缺失需阻断。这样避免把 intake、panel、summary 误读成真实送达成功。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“route/elevator 现场结果材料可复核、可追责、可回填”，但仍严格停在 software proof，不跨越真实硬件、真实现场、真实手机和真实外部云证据边界。

## 3. OKR 映射和 KR 拆解

- Objective 2：保持约 99%。本轮把 route/elevator result review intake 推进到 review decision，直接服务 KR2.4 / KR2.5 / KR2.6 / KR2.7 的错误原因、任务记录、elevator evidence 和人工接管材料链；但没有真实送达或真实电梯 field pass。
- Objective 3：保持约 99%。本轮把 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result 的缺口转成 review decision / rerun 指引；但没有真实路线实跑、真实 completion signal 或真实 task record。
- Objective 4：保持约 99%。mobile/web 增加只读“路线/电梯结果复核决策” panel，保持 Start Delivery、Confirm Dropoff、Cancel gating 不变；但没有真实手机/browser 或 production app 验收。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof。
- Objective 1：保持约 81%。本轮没有真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report。

## 4. 验收结果

Worker 已报告的分任务验证：

```text
Task A Autonomy:
focused unittest: Ran 5 tests OK
boundary: software_proof_docker_route_task_field_retest_result_review_decision_gate

Task B Robot:
diagnostics unittest: Ran 170 tests OK
aliases: route_task_field_retest_result_review_decision / route_task_field_retest_result_review_decision_summary / robot_diagnostics_route_task_field_retest_result_review_decision_summary

Task C Full-stack:
mobile unittest: Ran 66 tests OK
node --check mobile/web/app.js: pass
```

Task D Product 复跑组合围栏的最终结果记录在 `final.md`。本文件创建时保持本轮边界词：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 偏差和剩余风险

本轮没有把 Objective 2 / 3 从约 99% 上调到 100%。理由是本轮是 Docker-only / PC-only / metadata-only / read-only mobile software proof，只证明 review decision 合同、diagnostics 消费和手机只读展示可用，不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

剩余证据链：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime log。
- 真实 route completion signal 和真实 task record。
- 真实电梯门状态、目标楼层确认、人工协助记录。
- 真实 dropoff completion、cancel completion 和 delivery result。
- 真实 WAVE ROVER/UART/HIL packet。
- 真实 iPhone/Android browser、production app、真实 PWA prompt/user choice。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/cutover。
