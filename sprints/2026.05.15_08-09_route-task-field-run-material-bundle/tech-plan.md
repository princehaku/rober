# Sprint 2026.05.15_08-09 Route Task Field Run Material Bundle - Tech Plan

sprint_type: epic

## 1. 技术方案

在 `route_task_field_run_evidence_kit` 之后增加 material bundle。Autonomy 负责生成 bundle summary 和 material directory scaffold；Robot 负责 diagnostics metadata-only consumption；Full-stack 负责 mobile read-only panel；Product 负责验收、OKR 和 closeout。

## 2. 文件范围

Task A - Autonomy Algorithm Engineer：

- `pc-tools/evidence/route_task_field_run_material_bundle.py`
- `pc-tools/evidence/test_route_task_field_run_material_bundle.py`
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

- `sprints/2026.05.15_08-09_route-task-field-run-material-bundle/tech-done.md`
- `sprints/2026.05.15_08-09_route-task-field-run-material-bundle/side2side_check.md`
- `sprints/2026.05.15_08-09_route-task-field-run-material-bundle/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 接口契约

- 新 schema：`trashbot.route_task_field_run_material_bundle.v1`。
- 新 summary schema：`trashbot.route_task_field_run_material_bundle_summary.v1`。
- 新 boundary：`software_proof_docker_route_task_field_run_material_bundle_gate`。
- 新 diagnostics/mobile 摘要必须保持 `primary_actions_enabled=false`、`delivery_success=false`、`same_evidence_ref_required=true`。
- Material bundle 可引用上一轮 evidence kit，但不得暴露 raw local path；面向手机和 diagnostics 的 ref 必须是 safe ref 或 basename。
- Material directory scaffold 至少包含 route/task/completion/operator notes/diagnostics/mobile summary 的模板或占位文件，并在 summary 里列出生成状态。

## 4. 验收命令

Task A：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_run_material_bundle.py pc-tools/evidence/test_route_task_field_run_material_bundle.py
python3 pc-tools/evidence/test_route_task_field_run_material_bundle.py
python3 pc-tools/evidence/route_task_field_run_material_bundle.py --help
rg -n "trashbot.route_task_field_run_material_bundle.v1|software_proof_docker_route_task_field_run_material_bundle_gate|delivery_success=false|same_evidence_ref_required" pc-tools/evidence docs/navigation pc-tools/README.md
git diff --check -- pc-tools/evidence/route_task_field_run_material_bundle.py pc-tools/evidence/test_route_task_field_run_material_bundle.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

Task B：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_run_material_bundle|software_proof_docker_route_task_field_run_material_bundle_gate|delivery_success" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C：

```bash
python3 mobile/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_material_bundle|现场材料包|delivery_success=false|primary_actions_enabled=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D：

```bash
test -f sprints/2026.05.15_08-09_route-task-field-run-material-bundle/tech-done.md
test -f sprints/2026.05.15_08-09_route-task-field-run-material-bundle/side2side_check.md
test -f sprints/2026.05.15_08-09_route-task-field-run-material-bundle/final.md
rg -n "software_proof_docker_route_task_field_run_material_bundle_gate|Objective 2|Objective 3|Objective 5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_08-09_route-task-field-run-material-bundle
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_08-09_route-task-field-run-material-bundle
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对该最低 Objective：否，主攻 Objective 2 / Objective 3。
3. 不针对 Objective 5 的理由：Objective 5 下一步必须依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部材料。本机只有 Docker，继续做本地 O5 metadata depth 会重复消费同一 blocker。`OKR.md` 第 6 节也明确要求外部材料不可用时，不要重复本地 O5 metadata depth，改把 route/task evidence kit 走向真实 Nav2/fixed-route 或同一 `evidence_ref` 上车复账材料。

## 6. 风险边界

- 本轮 material bundle 仍可能只是现场执行前准备，不等于现场执行。
- 如果 worker 发现 evidence kit schema 不足，优先做向后兼容读取，不扩大为重构。
- 如果 Browser 插件不可用，只记录不能计真实 browser/手机 proof，不阻塞 unit/syntax 围栏。
