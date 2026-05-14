# Sprint 2026.05.15_04-05 Route Task Field Run Reconciliation - Tech Done

sprint_type: epic

## 1. 实际改动

本 sprint 完成 `software_proof_docker_route_task_field_run_reconciliation_gate`，把上一轮 execution pack 推进为现场材料复账 verdict。A/B/C worker 已完成工程实现和各自围栏验证；Task D 仅做产品验收收口，未修改工程代码或测试。

Task A `autonomy-engineer` 改动：

- `pc-tools/evidence/route_task_field_run_reconciliation.py`
- `pc-tools/evidence/test_route_task_field_run_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task A 交付 dependency-free reconciliation CLI，支持 `--execution-pack-json`、`--intake-json`、`--output`、`--evidence-ref`、`--once-json`，输出 `schema=trashbot.route_task_field_run_reconciliation.v1`、`evidence_boundary=software_proof_docker_route_task_field_run_reconciliation_gate`、`same_evidence_ref_required=true`、`reconciliation_verdict`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task B `robot-software-engineer` 改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task B 新增 `route_task_field_run_reconciliation` / `route_task_field_run_reconciliation_summary` diagnostics metadata-only summary，支持 explicit ref 和 `TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION`；固定不触发 collect/dropoff/cancel、remote ACK、cursor/persistence、terminal ACK、Nav2、HIL、production readiness、dropoff/cancel completion 或 delivery success。

Task C `full-stack-software-engineer` 改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task C 新增只读“路线任务现场复账”panel，展示 verdict、safe `evidence_ref`、same ref、materials、operator next steps、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 boundary；缺 summary fail closed，不读取 raw artifact 或本机路径，不改变 Start/Confirm/Cancel gating。

Task D `product-okr-owner` 改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/tech-done.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/side2side_check.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/final.md`

## 2. 验证结果

Task A 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_reconciliation.py`：pass
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_reconciliation.py`：`Ran 8 tests OK`
- `python3 pc-tools/evidence/route_task_field_run_reconciliation.py --help`：pass
- required `rg`：pass
- scoped `git diff --check`：pass

Task B 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics`：`Ran 63 tests OK`
- required `rg`：pass
- scoped `git diff --check`：pass

Task C 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint`：`Ran 14 tests OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`：pass
- `node --check mobile/web/app.js`：pass
- required `rg`：pass
- scoped `git diff --check`：pass

Task D 产品收口验证：

- `rg -n "2026.05.15_04-05_route-task-field-run-reconciliation|software_proof_docker_route_task_field_run_reconciliation_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_04-05_route-task-field-run-reconciliation`：pass
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_04-05_route-task-field-run-reconciliation/tech-done.md sprints/2026.05.15_04-05_route-task-field-run-reconciliation/side2side_check.md sprints/2026.05.15_04-05_route-task-field-run-reconciliation/final.md`：pass

## 3. 偏差与失败定位

无未解决验证失败。Task D 只做限定文件范围内的产品 closeout，没有修改工程代码、测试、硬件配置、launch 参数或业务实现。

## 4. 剩余风险

`software_proof_docker_route_task_field_run_reconciliation_gate` 只证明 Docker/local reconciliation artifact、diagnostics metadata-only summary 和 mobile read-only panel 可生成、消费和展示。它不证明真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车实机复账、WAVE ROVER、真实串口/UART、HIL、dropoff/cancel completion、delivery success、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。

## 5. OKR 最低优先级回顾

本 sprint 针对启动时最低完成度 Objective 2 / Objective 3。收口后两者由约 63% 保守上调到约 64%；Objective 5 保持约 66%，因为本轮没有真实外部 O5 材料。下一轮仍应按 live `OKR.md` 4.1 重新排序。
