# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - Tech Done

sprint_type: epic

## 实际改动

Task A `autonomy-engineer`：

- 新增 `pc-tools/evidence/route_task_field_run_readiness.py` 和 `pc-tools/evidence/test_route_task_field_run_readiness.py`。
- 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- 交付 `schema=trashbot.route_task_field_run_readiness.v1`、`evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`、`same_evidence_ref_required=true`、`required_field_run_materials`、`commands_to_run`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false` 的 Docker/local readiness handoff。

Task B `robot-software-engineer`：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- diagnostics 仅 metadata-only 消费 `route_task_field_run_readiness` / summary；不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL 或 delivery success。

Task C `full-stack-software-engineer`：

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- 手机端新增只读“路线任务现场联跑准备”面板，消费 phone-safe readiness summary；不读取 raw artifact，不改变 Start/Confirm/Cancel gating。

Task D `product-okr-owner`：

- 更新本文件、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
- Objective 2 / Objective 3 均从约 82% 保守上调到约 83%；Objective 5 保持约 68%，Objective 1 保持约 75%，Objective 4 保持约 95%。

## 验证结果

Task A worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_readiness.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_readiness.py`：`Ran 5 tests OK`。
- `python3 pc-tools/evidence/route_task_field_run_readiness.py --help`：pass。
- 临时 JSON `--once-json`：pass，输出 `overall_status=ready_for_field_run_materials`、`evidence_ref=file:run-001.json`、`delivery_success=false`。
- required `rg`：pass。
- scoped `git diff --check`：pass；untracked 新文件额外 `git diff --check --no-index`：pass。

Task B worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics`：`Ran 55 tests OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Task C worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint`：`Ran 6 tests OK`。
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`：pass。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Task D Product 验收命令：

- `rg -n "2026.05.15_00-01_route-task-field-run-readiness|software_proof_docker_route_task_field_run_readiness_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL|Docker" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_00-01_route-task-field-run-readiness`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_00-01_route-task-field-run-readiness/tech-done.md sprints/2026.05.15_00-01_route-task-field-run-readiness/side2side_check.md sprints/2026.05.15_00-01_route-task-field-run-readiness/final.md`

结果：两条命令均 exit 0；`rg` 命中本轮 sprint、OKR/progress 目标关键词和边界词，`git diff --check` 无输出。

## 偏差和失败定位

- 未发现需要 Product 侧重试的工程失败。
- 本轮没有执行真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART 或 HIL；这与 sprint 范围一致。
- 本轮没有取得真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；Objective 5 不提升。

## 剩余风险

- `software_proof_docker_route_task_field_run_readiness_gate` 只证明 Docker/local readiness artifact、diagnostics metadata-only summary 和 mobile read-only panel 可形成下一次 field run handoff。
- 仍不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 下一轮若继续 O2/O3，必须拿真实现场材料补齐同一 `evidence_ref` 的 route status、task record、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary。
