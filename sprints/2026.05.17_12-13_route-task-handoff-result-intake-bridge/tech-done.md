# Sprint 2026.05.17_12-13 Route Task Handoff Result Intake Bridge - Tech Done

sprint_type: epic

## 1. 实际改动

本轮工程 worker 已完成 review-result handoff -> result-intake 的 software-proof bridge。Product closeout 只验收并更新留档、OKR 与进度日志；未改工程代码、测试、mobile fixture 或其他 sprint。

### Task A - Autonomy Algorithm Engineer

改动文件：

- `pc-tools/evidence/route_task_field_retest_result_intake.py`
- `pc-tools/evidence/test_route_task_field_retest_result_intake.py`
- `docs/navigation/fixed_route_workflow.md`
- `pc-tools/README.md`

结果：`route_task_field_retest_result_intake` 新增对 `trashbot.route_task_field_retest_review_result_handoff.v1` 与 `trashbot.route_task_field_retest_review_result_handoff_summary.v1` 的来源支持；source candidate 白名单支持显式 handoff artifact/summary、wrapper key 和 nested JSON key。输出仍保持 `trashbot.route_task_field_retest_result_intake.v1`、`trashbot.route_task_field_retest_result_intake_summary.v1` 与 `software_proof_docker_route_task_field_retest_result_intake_gate`，并继续固定八类 result materials，不让 upstream handoff 裁剪 required materials。

验证结果：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_intake.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_intake.py`：`Ran 14 tests in 0.055s OK`。
- `python3 pc-tools/evidence/route_task_field_retest_result_intake.py --help`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Task B - Robot Platform Engineer

改动文件：无代码改动。

结果：既有 `operator_gateway_diagnostics.py` 已能对 `route_task_field_retest_result_intake` file/env/top-level/nested summary 做 metadata-only 只读消费，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。本轮没有新增 ROS action/topic/service、launch 参数、硬件配置、`/cmd_vel` 控制路径或 primary action 放行。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 144 tests in 0.230s OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Task C - User Touchpoint Full-Stack Engineer

改动文件：

- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

结果：mobile fixture 标记 `source_review_result_handoff_schema`，focused assertion 确认 result-intake 可来自 review-result handoff，并仍保持 `delivery_success=false`、`primary_actions_enabled=false`。产品文档明确 mobile 只展示 normalized result-intake summary，不展示 upstream handoff artifacts。未改 `mobile/web/app.js` / `mobile/web/styles.css`，Start Delivery / Confirm Dropoff / Cancel gating 未变。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：`Ran 40 tests in 0.126s OK`。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

## 2. Product closeout 判断

用户价值：本轮把上一轮 `route_task_field_retest_review_result_handoff` 交接包接入既有 `route_task_field_retest_result_intake` gate，减少现场复测材料链断点。后续真实材料到来时，现场团队可直接用 handoff artifact / summary / wrapper / nested JSON 生成 result-intake artifact / summary，不需要人工改写 schema。

OKR 映射：

- Objective 2：PR #4 route/elevator field-material 链路从 review-result handoff 推进到 result-intake 可消费桥，支持后续 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 的同一 `evidence_ref` 回填；保守从约 92% 上调到约 93%。
- Objective 3：Nav2/fixed-route runtime log、route completion signal、task record 等八类 result materials 没有被 upstream handoff 裁剪，result-intake gate 仍能要求同一 `evidence_ref` 的完整材料；保守从约 92% 上调到约 93%。
- Objective 1：无真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 PR #5 真实 2D LiDAR / ToF 材料；保持约 77%。
- Objective 4：mobile 只补 fixture/assertion 与产品说明，没有真实手机/browser、production app、PWA prompt/user choice 或现场 phone behavior；保持约 99%。
- Objective 5：仍约 68%，本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof；继续不把本地 bridge 写成 O5 progress。

## 3. 验证结果

Product closeout 已运行：

```bash
rg -n "route_task_field_retest_review_result_handoff|route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
```

最终输出见本轮最终回复；两条 closeout 验收命令通过。

## 4. 剩余风险

- 本轮证据边界是 `software_proof_docker_route_task_field_retest_result_intake_gate`，不是真实 route/elevator field pass。
- `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 仍必须保持；Robot/mobile 只读消费不能被解释为动作授权。
- 仍缺真实 Nav2/fixed-route runtime、真实 route completion signal、真实 task record、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel completion、真实 delivery result、真实手机/browser、WAVE ROVER、真实串口/UART、HIL 和 Objective 5 external proof。
