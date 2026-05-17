# Sprint 2026.05.17_19-20 Route Task Result Callback Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_result_callback_review_decision`，承接上一轮 `route_task_field_retest_result_callback_intake`，把 callback packet 摄取后的 accepted/missing/rejected updates 转成下一步可执行的复核决策。

Task A / Autonomy Algorithm Engineer：

- 新增 PC gate `pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py`。
- 新增 focused unittest `pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py`。
- 更新 `docs/interfaces/evidence_contracts.md`，记录 `trashbot.route_task_field_retest_result_callback_review_decision.v1` / `_summary.v1`。

Task B / Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，新增 diagnostics metadata-only consumer。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

Task C / User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`，新增只读“路线任务回调复核决策” panel。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

Task D / Product Manager / OKR Owner：

- 更新 `OKR.md` 当前快照，最新 sprint 改为 `2026.05.17_19-20_route-task-result-callback-review-decision`。
- 更新 `docs/process/okr_progress_log.md` 顶部进度日志。
- 新增本 `tech-done.md`、`side2side_check.md` 和 `final.md` closeout 链路。

## 2. 验证结果

Task A / Autonomy：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py` pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py` pass，关键输出：`Ran 6 tests OK`。
- `python3 pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py --help` pass。
- required `rg` pass。
- scoped `git diff --check` pass。

Task B / Robot：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` pass，关键输出：`Ran 156 tests OK`。
- required `rg` pass。
- scoped `git diff --check` pass。

Task C / Full-stack：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` pass，关键输出：`Ran 52 tests OK`。
- `node --check mobile/web/app.js` pass。
- required `rg` pass。
- scoped `git diff --check` pass。

Task D / Product：

- `rg -n "route_task_field_retest_result_callback_review_decision|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision` pass。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-done.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/side2side_check.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md` pass。

## 3. 证据边界

本轮边界固定为 `software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`。

本轮只证明当前 repo 内 PC gate、Robot diagnostics metadata-only consumer 和 mobile/web read-only panel 能在 Docker-only/local software proof 边界内 fail closed 地表达 callback review decision。它不是真实 route/elevator field pass，不是真实 Nav2/fixed-route，不是真实 task record/completion signal，不是真实手机/browser，不是真实 WAVE ROVER/UART/HIL，也不是真实 Objective 5 external proof。

所有面均必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 偏差

无功能范围偏差。Product closeout 没有修改 A/B/C 的代码、测试或接口文档。

OKR 数字偏差：Objective 2 / 3 / 4 已处于约 99% 的软件证明上限，本轮只补充 review-decision 证据，不继续上调；Objective 5 仍约 68%，没有真实 external proof，不虚增。

## 5. 剩余风险

- 仍缺真实现场 callback packet、真实材料回填和同一 `evidence_ref` 上车复账。
- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- 仍缺真实电梯门状态、真实楼层确认、真实人工协助记录、真实喇叭/TTS 和真实送达。
- 仍缺真实手机设备 / iPhone / Android / production app / PWA prompt/user choice 现场验收。
- 仍缺 Objective 5 所需公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- 仍缺 PR #5 真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定与 HIL-entry 材料。
