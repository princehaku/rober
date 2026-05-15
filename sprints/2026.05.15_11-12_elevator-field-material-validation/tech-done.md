# Sprint 2026.05.15_11-12 Elevator Field Material Validation - Tech Done

sprint_type: epic

## 1. 实际改动

Task A Autonomy 完成电梯现场材料校验 CLI：

- 新增 `pc-tools/evidence/elevator_field_run_material_validation.py`。
- 新增 `pc-tools/evidence/test_elevator_field_run_material_validation.py`。
- 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/product/elevator_assisted_delivery.md`。
- 输出 `schema=trashbot.elevator_field_run_material_validation.v1`、`summary_schema=trashbot.elevator_field_run_material_validation_summary.v1`、`evidence_boundary=software_proof_docker_elevator_field_material_validation_gate`。
- 校验 door state、target floor confirmation、human assistance/operator note、Nav2/fixed-route runtime log、task record、completion signal、diagnostics/mobile safe summary 是否缺失、模板、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true`，并 fail closed。

Task B Robot 完成 diagnostics 只读消费：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 支持 explicit ref 和 `TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION` / `TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY`。
- 暴露 `elevator_field_run_material_validation` / `elevator_field_run_material_validation_summary`，固定 `delivery_success=false`、`primary_actions_enabled=false`，不触发 collect/dropoff/cancel、ACK、Nav2、HIL 或真实送达。

Task C Full-stack 完成手机只读 panel：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“电梯现场材料校验” panel，兼容 top-level、`phone_readiness`、diagnostics summary 和 nested diagnostics summary。
- 展示 validation status、safe `evidence_ref`、missing/template/mismatch categories、operator next steps、`not_proven`、boundary 和 `delivery_success=false / primary_actions_enabled=false`，不改变 Start/Confirm/Cancel gating。

Task D Product 完成本 closeout：

- 更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Autonomy 围栏：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/elevator_field_run_material_validation.py pc-tools/evidence/test_elevator_field_run_material_validation.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_field_run_material_validation.py`：`Ran 7 tests ... OK`。
- `python3 pc-tools/evidence/elevator_field_run_material_validation.py --help`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Robot 围栏：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 75 tests ... OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Full-stack 围栏：

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py`：`Ran 42 tests ... OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py`：pass。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。
- Browser render check 未运行：Browser runtime reported `Browser is not available: iab`。

Product 围栏：

- `rg -n "elevator_field_run_material_validation|software_proof_docker_elevator_field_material_validation_gate|not real|不证明|delivery_success=false|Objective 5" sprints/2026.05.15_11-12_elevator-field-material-validation OKR.md docs/process/okr_progress_log.md`：pass。
- `git diff --check -- sprints/2026.05.15_11-12_elevator-field-material-validation OKR.md docs/process/okr_progress_log.md`：pass。

## 3. 偏差与失败定位

- Browser render check 未能执行，原因是当前 Browser runtime 不可用：`Browser is not available: iab`。因此本轮不能声称真实手机/browser、production app、PWA prompt/user choice 或视觉渲染验收通过。
- 当前本机没有真实硬件，只有 Docker。本轮不访问真实电梯、真实 ROS graph、真实 Nav2/fixed-route runtime、WAVE ROVER、UART、HIL、真实 dropoff/cancel completion 或 delivery success。
- 本轮未获得真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料，因此不推进 Objective 5。

## 4. 剩余风险

- `software_proof_docker_elevator_field_material_validation_gate` 只证明 Docker/local material validation artifact、Robot diagnostics metadata-only summary、mobile read-only panel 和只读控制边界可工作。
- 不证明真实电梯、真实楼层确认、真实人工协助、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/UART/HIL、同一 `evidence_ref` 上车实机复账、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- 下一轮要真正推进现场闭环，必须回填同一 `evidence_ref` 下的真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、diagnostics/mobile safe summary，并继续保持 `delivery_success=false`，直到真实证据完整通过。
