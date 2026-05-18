# Sprint 2026.05.18_12-13 Route Task Acceptance Execution Callback Intake - Tech Done

## Autonomy Algorithm Engineer

### 自主能力目标和本轮抓手

本轮 Autonomy 抓手是新增 `route_task_field_retest_acceptance_execution_callback_intake` PC evidence gate，把上一轮 acceptance execution pack 与现场 safe callback packet 复账成可被 Robot diagnostics / mobile/web 只读消费的 artifact 和 summary。证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### 实际改动

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_acceptance_execution_callback_intake.py`。
- 新增 `tests/test_route_task_field_retest_acceptance_execution_callback_intake.py`。
- 更新 `docs/interfaces/evidence_contracts.md` 的 callback intake contract。
- 更新 `pc-tools/README.md` 的 PC gate 使用说明。

### 验证结果

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py tests/test_route_task_field_retest_acceptance_execution_callback_intake.py`：通过，无输出。
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_intake`：通过，`Ran 5 tests in 0.101s`，`OK`。
- `python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py --help`：通过，显示 `--acceptance-execution-pack-json`、`--callback-json`、`--evidence-ref`、`--output`、`--summary-output` 和 `--once-json`。
- `rg -n "route_task_field_retest_acceptance_execution_callback_intake|software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake`：通过，命中新 gate、测试、docs 和 sprint 留档。
- `git diff --check -- pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake`：通过，无输出。

第一轮 unittest 暴露材料名漂移：测试 callback 使用了 `nav2_fixed_route_runtime_log`，而 execution pack contract 的规范字段是 `nav2_or_fixed_route_runtime_log`。已修正测试 fixture，避免把同一材料误判为缺项。

### 剩余风险

本 gate 只证明 Docker/local software proof 下的 safe callback packet 复账能力；不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## Robot Platform Engineer

### Robot diagnostics 目标和边界

Robot diagnostics 新增 `route_task_field_retest_acceptance_execution_callback_intake` metadata-only consumer，支持 direct artifact、summary wrapper、nested diagnostics wrapper，以及 explicit ref / env source。`status_payload` 现在输出 `route_task_field_retest_acceptance_execution_callback_intake`、`route_task_field_retest_acceptance_execution_callback_intake_summary`、`robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary` 三个 safe alias。边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### 实际改动

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：新增 schema/gate 常量、默认 blocked summary、source contract、same-`evidence_ref` 检查、disabled-actions 检查、not_proven 列表、summarizer，以及 `build_diagnostics_payload` 的 source/env/status alias 接入。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：覆盖 alias 相等、direct artifact、summary-only env source、nested wrapper、missing input、unsupported schema/boundary、same-`evidence_ref` mismatch、unsafe success/control wording 和 enabled primary actions fail-closed。
- 更新 `docs/interfaces/ros_contracts.md`：记录 Robot diagnostics 新 alias、source/env 入口、可展示字段和不触发 Start Delivery / Confirm Dropoff / Cancel / ACK / Nav2 / HIL / delivery success 的边界。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，无输出。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，`Ran 181 tests in 0.360s`，`OK`。
- `rg -n "route_task_field_retest_acceptance_execution_callback_intake|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake`：通过，命中 Robot diagnostics、tests、ROS contract 和 sprint 留档。

第一轮 unittest 暴露 unsupported schema 会先落入 `missing_summary`。已修正带 schema/boundary 的非匹配对象进入 `unsupported_schema` 分支，避免接错 gate 时定位不清。

### 剩余风险

本次只证明 Robot diagnostics 能安全消费 repo-local metadata summary；不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、ACK、HIL、真实串口/WAVE ROVER feedback、真实手机/browser 或 Objective 5 external proof。Product 需在最终收口时核对 Autonomy、Robot、Full-stack 三端字段一致性；无需 Hardware 协同，除非下一轮进入真实设备或串口材料。

## User Touchpoint Full-Stack Engineer

### 用户旅程变化和触点收益

mobile/web 新增只读“现场复测验收执行回调入口”panel，放在 acceptance execution pack 后，优先读取 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary`，再读取普通 summary / artifact。用户可在手机端看到 safe `evidence_ref`、source execution pack、callback packet status、received/missing/rejected materials、owner next steps、next required evidence、safe copy 和 boundary flags；Start Delivery、Confirm Dropoff、Cancel 仍保持 fail-closed，不被该 panel 打开。

### 实际改动

- 更新 `mobile/web/app.js`：新增 `route_task_field_retest_acceptance_execution_callback_intake` candidate / safe text / summary / panel / render / whitelist copy-export 逻辑。
- 更新 `mobile/web/fixtures/status.json` 与 `mobile/fixtures/mobile_web_status.fixture.json`：新增 artifact、summary、Robot diagnostics safe alias fixture，固定 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`：覆盖 panel 位置、Robot alias 优先级、copy/export 白名单、两套 fixture 和 unsafe 字段围栏。
- 更新 `docs/product/mobile_user_flow.md`：补充手机端执行回调入口的消费来源、展示字段、copy/export 白名单和证据边界。

### 验证结果

- `node --check mobile/web/app.js`：通过，无输出。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：通过，`Ran 78 tests in 0.402s`，`OK`。
- `rg -n "route_task_field_retest_acceptance_execution_callback_intake|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake`：通过，命中新 panel、fixture、产品文档和 sprint 留档。
- `git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake`：通过，无输出。

### 剩余风险

本次只完成 mobile/web 对 safe callback intake summary 的只读消费和 copy/export 白名单证明；不证明真实路线/电梯现场材料、真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 delivery result、真实手机设备/browser、HIL 或 Objective 5 external proof。Robot 侧仍需稳定发布同名 safe alias，Autonomy/现场 owner 仍需提供同一 safe `evidence_ref` 的真实材料。
