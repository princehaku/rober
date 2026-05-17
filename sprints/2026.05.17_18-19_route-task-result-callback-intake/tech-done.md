# Sprint 2026.05.17_18-19 Route Task Result Callback Intake - Tech Done

sprint_type: epic

## 1. 完成结论

状态：`DONE_SOFTWARE_PROOF_ONLY`。

本轮 A/B/C workers 已完成 durable work，并把 `route_task_field_retest_result_callback_intake` 从上一轮现场派发推进到 callback packet 摄取。证据边界固定为 `software_proof_docker_route_task_field_retest_result_callback_intake_gate`，所有 PC / Robot / mobile 输出继续保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮不是真实 route/elevator field pass，不是真实 Nav2/fixed-route 运行，不是真实手机/browser，不是 WAVE ROVER/UART/HIL，也不是 Objective 5 external proof。

## 2. 实际改动

Task A / Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_retest_result_callback_intake.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py`。
- 更新 `docs/interfaces/evidence_contracts.md`。
- 产出 `trashbot.route_task_field_retest_result_callback_intake.v1` / `_summary.v1`，支持 dispatch artifact / summary 与 callback packet safe sample 摄取。
- 校验同一 `safe_evidence_ref`、owner work orders fulfilment、callback packet requirements、accepted/missing/rejected updates 和 owner follow-up。

Task B / Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 diagnostics metadata-only consumer，支持 file/env/top-level/nested callback intake summary。
- 未改变 task_orchestrator、action server、Start、Dropoff、Cancel、ACK、cursor、Nav2 或 HIL 控制语义。

Task C / User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增 mobile/web 只读“路线任务回调入口” panel，展示 callback intake status、accepted/missing/rejected updates、owner follow-up、safe evidence ref 和边界 flags。
- copy/export 继续要求 backend-provided `safe_copy`，缺失显示 `blocked copy unavailable`；Start/Confirm/Cancel gating 不变。

Task D / Product Manager / OKR Owner：

- 更新 `OKR.md` 当前进度快照：Objective 2 / Objective 3 从约 98% 保守上调到约 99%，Objective 5 保持约 68%。
- 更新 `docs/process/okr_progress_log.md`，记录本轮证据、验证和边界。
- 创建本 `tech-done.md`，并补齐 `side2side_check.md` 与 `final.md`。

## 3. 验证结果

Task A / Autonomy：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_callback_intake.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py
Ran 5 tests in 0.141s
OK

python3 pc-tools/evidence/route_task_field_retest_result_callback_intake.py --help
pass

required rg
pass

git diff --check -- pc-tools/evidence/route_task_field_retest_result_callback_intake.py pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py docs/interfaces/evidence_contracts.md
pass
```

Task B / Robot：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 154 tests in 0.239s
OK

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
pass
```

Task C / Full-stack：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 50 tests ... OK

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
pass
```

Task D / Product closeout：

```text
rg -n "route_task_field_retest_result_callback_intake|software_proof_docker_route_task_field_retest_result_callback_intake_gate|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_18-19_route-task-result-callback-intake
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-done.md sprints/2026.05.17_18-19_route-task-result-callback-intake/side2side_check.md sprints/2026.05.17_18-19_route-task-result-callback-intake/final.md
pass

test -f tech-done.md && test -f side2side_check.md && test -f final.md
pass
```

## 4. 偏差

- 无实现范围偏差：Product closeout 只更新指定 Product 范围文件，未修改 PC / Robot / mobile 代码、测试或接口文档。
- 无证据边界偏差：本轮没有把 Docker-only software proof 写成真实 field pass、HIL、真实手机或 Objective 5 external proof。
- 无提交：本轮按任务要求不 commit，由主会话后续做 final integration commit/push。

## 5. 剩余风险

- Objective 5 仍是数值最低 Objective，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，不能提升。
- PR #4 route/elevator 仍缺真实现场材料：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- PR #5 仍缺真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料。
- 当前所有新增能力仍是 PC-only / metadata-only / read-only mobile software proof，不能代替真实上车验证。
