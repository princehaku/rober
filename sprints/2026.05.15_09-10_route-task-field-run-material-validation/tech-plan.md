# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - Tech Plan

sprint_type: epic

## 1. 方案

本轮沿上一轮 material bundle 继续做一层 validation gate。PC 侧生成 validation artifact；Robot diagnostics 只读消费；mobile/web 只读展示。所有链路都保留 `primary_actions_enabled=false`、`delivery_success=false`、`same_evidence_ref_required=true` 和 `not_proven`。

## 2. 任务分工

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_run_material_validation.py`
- `pc-tools/evidence/test_route_task_field_run_material_validation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

要求：

- 新增 dependency-free CLI，读取 material bundle 与 `--material-dir`。
- 输出 artifact + summary schema：`trashbot.route_task_field_run_material_validation.v1` / `trashbot.route_task_field_run_material_validation_summary.v1`。
- 对模板未替换、缺材料、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe copy、delivery success claim、primary actions claim fail closed。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_run_material_validation.py pc-tools/evidence/test_route_task_field_run_material_validation.py
python3 pc-tools/evidence/test_route_task_field_run_material_validation.py
python3 pc-tools/evidence/route_task_field_run_material_validation.py --help
rg -n "software_proof_docker_route_task_field_run_material_validation_gate|trashbot.route_task_field_run_material_validation.v1|delivery_success=false" pc-tools/evidence/route_task_field_run_material_validation.py pc-tools/evidence/test_route_task_field_run_material_validation.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_run_material_validation.py pc-tools/evidence/test_route_task_field_run_material_validation.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

要求：

- metadata-only 消费 Task A artifact / summary。
- 支持 explicit ref 与 `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION` / `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY`。
- schema/boundary/unsafe/claim mismatch 必须 fail closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "software_proof_docker_route_task_field_run_material_validation_gate|route_task_field_run_material_validation|TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

要求：

- 新增只读“路线材料校验” panel。
- 从 status、phone_readiness、diagnostics summary 等安全路径读取 validation summary。
- 展示 status、safe evidence ref、missing/placeholder/mismatch materials、operator next steps、`not_proven` 和 boundary。
- 不改变 Start / Confirm / Cancel gating。

验收命令：

```bash
python3 mobile/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_route_task_field_run_material_validation_gate|route_task_field_run_material_validation|路线材料校验" mobile/web/index.html mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

文件范围：

- `sprints/2026.05.15_09-10_route-task-field-run-material-validation/tech-done.md`
- `sprints/2026.05.15_09-10_route-task-field-run-material-validation/side2side_check.md`
- `sprints/2026.05.15_09-10_route-task-field-run-material-validation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
rg -n "software_proof_docker_route_task_field_run_material_validation_gate|Objective 2|Objective 3|not real|不证明" sprints/2026.05.15_09-10_route-task-field-run-material-validation OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.15_09-10_route-task-field-run-material-validation OKR.md docs/process/okr_progress_log.md
```

## 3. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective 是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：`OKR.md` 第 6 节和最近 `08-09` final 都说明 O5 继续上调需要真实外部材料；本机只有 Docker，没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。继续做本地 O5 metadata 会重复消费同一 blocker。当前最高可行动作是沿 Objective 2 / Objective 3，把 material bundle 推进为现场材料校验，服务下一次真实 route/task field run。

## 4. 证据边界

本轮只允许声明 `software_proof_docker_route_task_field_run_material_validation_gate`。不得声明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 外部 proof。
