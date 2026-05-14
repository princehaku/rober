# Sprint 2026.05.15_01-02 Route Task Field Run Intake Crosscheck - Tech Done

sprint_type: epic

## 1. 实际改动

本轮交付 `software_proof_docker_route_task_field_run_intake_crosscheck_gate`，把上一轮 route/task field-run readiness handoff 推进到同一 `evidence_ref` 下的现场材料 intake/crosscheck 软件复账能力。

### Task A - `autonomy-engineer`

- 新增 `pc-tools/evidence/route_task_field_run_intake.py`。
- 新增 `pc-tools/evidence/test_route_task_field_run_intake.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 交付 schema `trashbot.route_task_field_run_intake_crosscheck.v1`。
- 交付 boundary `software_proof_docker_route_task_field_run_intake_crosscheck_gate`。
- CLI 支持五输入 JSON：route status、task record、runtime log、robot-side task evidence、support-safe mobile summary。
- 输出 `missing_materials`、`mismatch_reasons`、`commands_to_rerun`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### Task B - `robot-software-engineer`

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- diagnostics 新增 `route_task_field_run_intake` / `route_task_field_run_intake_summary` metadata-only summary。
- 支持 explicit `route_task_field_run_intake_ref` 和环境变量 `TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE`。
- 只白名单输出 phone-safe status、`evidence_ref`、missing、mismatch、commands、`not_proven` 和 boundary。
- 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、Nav2、HIL、dropoff/cancel completion 或 delivery success。

### Task C - `full-stack-software-engineer`

- 更新 `mobile/web/index.html`。
- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“路线任务现场材料复核” panel。
- 消费 `route_task_field_run_intake` / `route_task_field_run_intake_summary` / nested diagnostics compatible summary。
- 展示 status、safe `evidence_ref`、missing/mismatch、`commands_to_rerun`、`not_proven` 和 boundary。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 集成修复补齐 Task B nested `crosscheck.status`、`missing_materials`、`mismatch_reasons`、`commands_to_rerun` 消费。

## 2. 验证结果

### Task A 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_intake.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_intake.py`：`Ran 6 tests OK`。
- `python3 pc-tools/evidence/route_task_field_run_intake.py --help`：pass。
- 五份临时材料同 `evidence_ref` `--once-json` drill：输出 `overall_status=ready_for_review`、`missing_materials=[]`、`mismatch_reasons=[]`、`delivery_success=false`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Task B 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics`：`Ran 57 tests OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Task C 验证

- 初次验证：mobile unittest `Ran 8 tests OK`、py_compile pass、`node --check mobile/web/app.js` pass、required `rg` pass、scoped diff check pass。
- 集成修复后复验：mobile unittest `Ran 8 tests in 0.022s OK`、py_compile pass、`node --check mobile/web/app.js` pass、relevant `rg` pass、scoped diff check pass。

### 主会话只读集成核对

- schema/boundary 在 pc-tools、diagnostics、mobile 和 docs 中一致。
- 改动文件范围符合本 sprint 允许范围和收口文档范围。
- `route_task_field_run_intake` 只作为 intake/crosscheck、diagnostics metadata-only summary 和 mobile read-only panel 使用。

## 3. 偏差与失败定位

- 初始 Task C mobile resolver 尚未覆盖 Task B nested `crosscheck.status`、`missing_materials`、`mismatch_reasons`、`commands_to_rerun` shape。
- 定位后已由 `full-stack-software-engineer` 补齐 nested diagnostics compatible summary 消费，并完成复验。
- 未发现需要回滚或扩大文件范围的问题。

## 4. 证据边界与剩余风险

本轮证据边界是 Docker/local software proof：`software_proof_docker_route_task_field_run_intake_crosscheck_gate`。

本轮不证明：

- 真实 Nav2/fixed-route。
- 真实路线采集。
- WAVE ROVER。
- 真实串口/UART。
- HIL 或真实 `hil_pass`。
- 同一 `evidence_ref` 上车复账。
- dropoff/cancel completion。
- delivery success。
- Objective 5 external proof。
- 公网 HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- worker/migration。

剩余风险：下一步必须拿到真实 route status、task record、runtime log、robot-side task evidence 和 mobile summary 后，才能把本轮 intake/crosscheck 用于真实 field run 复账；当前 `ready_for_review` 只表示材料形状可进入人工复核，不表示真实送达。
