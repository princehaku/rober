# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮在 `route_task_field_run_console` 之后增加一层 evidence kit。Autonomy 负责生成 artifact；Robot 负责 diagnostics metadata-only consumption；Full-stack 负责 mobile read-only panel；Product 负责验收、OKR 和 closeout。

## 2. 文件范围

Task A - Autonomy Algorithm Engineer：

- `pc-tools/evidence/route_task_field_run_evidence_kit.py`
- `pc-tools/evidence/test_route_task_field_run_evidence_kit.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task B - Robot Platform Engineer：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C - User Touchpoint Full-Stack Engineer：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task D - Product Manager / OKR Owner：

- `sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/tech-done.md`
- `sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/side2side_check.md`
- `sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 接口契约

- 新 schema：`trashbot.route_task_field_run_evidence_kit.v1`。
- 新 boundary：`software_proof_docker_route_task_field_run_evidence_kit_gate`。
- 新 diagnostics/mobile 摘要必须保持 `primary_actions_enabled=false`、`delivery_success=false`、`same_evidence_ref_required=true`。
- Evidence kit 可引用上一轮 `route_task_field_run_console`，但不得暴露 raw local path；面向手机和 diagnostics 的 ref 必须是 safe ref 或 basename。

## 4. 验收命令

Task A：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_run_evidence_kit.py pc-tools/evidence/test_route_task_field_run_evidence_kit.py
python3 pc-tools/evidence/test_route_task_field_run_evidence_kit.py
python3 pc-tools/evidence/route_task_field_run_evidence_kit.py --help
rg -n "trashbot.route_task_field_run_evidence_kit.v1|software_proof_docker_route_task_field_run_evidence_kit_gate|delivery_success=false|same_evidence_ref_required" pc-tools/evidence docs/navigation pc-tools/README.md
git diff --check -- pc-tools/evidence/route_task_field_run_evidence_kit.py pc-tools/evidence/test_route_task_field_run_evidence_kit.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

Task B：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_run_evidence_kit|software_proof_docker_route_task_field_run_evidence_kit_gate|delivery_success" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C：

```bash
python3 mobile/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_evidence_kit|路线现场证据包|delivery_success=false|primary_actions_enabled=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D：

```bash
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/tech-done.md
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/side2side_check.md
test -f sprints/2026.05.15_07-08_route-task-field-run-evidence-kit/final.md
rg -n "software_proof_docker_route_task_field_run_evidence_kit_gate|Objective 2|Objective 3|Objective 5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_07-08_route-task-field-run-evidence-kit
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_07-08_route-task-field-run-evidence-kit
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 2、Objective 3、Objective 5，均约 66%。
2. 本 sprint 是否针对最低 Objective：是，针对 Objective 2 / Objective 3。
3. 不针对 Objective 5 的理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部材料。本机只有 Docker，继续做本地 metadata depth 不会形成可信 O5 进度。

## 6. 风险边界

- 本轮 evidence kit 仍可能只是现场执行前准备，不等于现场执行。
- 如果 worker 发现上一轮 console schema 不足，优先做向后兼容读取，不扩大为重构。
- 如果 Browser 插件不可用，只记录不能计真实 browser/手机 proof，不阻塞 unit/syntax 围栏。
