# Sprint 2026.05.15_08-09 Route Task Field Run Material Bundle - Tech Done

sprint_type: epic

## 1. 实际改动

本轮围绕 `software_proof_docker_route_task_field_run_material_bundle_gate` 完成三条工程交付线，并由 Product 负责收口 OKR 与 sprint 留档。

Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_run_material_bundle.py`。
- 新增 `pc-tools/evidence/test_route_task_field_run_material_bundle.py`。
- 更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
- 功能结果：读取上一轮 `trashbot.route_task_field_run_evidence_kit.v1`，输出 `trashbot.route_task_field_run_material_bundle.v1` 与 `trashbot.route_task_field_run_material_bundle_summary.v1`；指定 `--material-dir` 时创建 route、task、completion、operator notes、diagnostics、mobile summary 模板或占位文件。

Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 功能结果：diagnostics metadata-only 消费 material bundle / summary，支持 explicit ref 与 `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE` / `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY`，schema 或 boundary 不匹配时 fail closed。

User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json` 与 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 功能结果：`mobile/web` 新增只读“路线现场材料包” panel，展示 safe `evidence_ref`、bundle status、模板文件、缺口、operator next steps、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 与 boundary，不改变 Start / Confirm / Cancel gating。

Product Manager / OKR Owner：

- 新增本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 与 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Autonomy 验证：

```text
python3 -m py_compile pc-tools/evidence/route_task_field_run_material_bundle.py pc-tools/evidence/test_route_task_field_run_material_bundle.py
pass

python3 pc-tools/evidence/test_route_task_field_run_material_bundle.py
Ran 7 tests OK

python3 pc-tools/evidence/route_task_field_run_material_bundle.py --help
pass

required rg
pass

scoped git diff --check
pass
```

Robot 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
pass

python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 71 tests OK

required rg
pass

scoped git diff --check
pass
```

Full-stack 验证：

```text
python3 mobile/test_mobile_web_entrypoint.py
Ran 39 tests OK

python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

scoped git diff --check
pass
```

Product closeout 需要在本文件落地后执行 Task D 验收命令。

## 3. 偏差与边界

本轮按计划形成 `software_proof_docker_route_task_field_run_material_bundle_gate`。产品判断上，Objective 2 与 Objective 3 可各从约 67% 保守上调到约 68%，因为 field-run evidence kit 已推进为可落目录、可回填、可交接的现场材料包，并进入 Robot diagnostics 与手机只读面板。

Objective 5 仍约 66%，继续是当前数值最低 Objective，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他外部材料，因此不提升 O5。

本轮不证明：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集。
- WAVE ROVER、串口/UART、Orange Pi 或 HIL。
- 同一 `evidence_ref` 的上车实机复账。
- 真实 dropoff completion、真实 cancel completion 或 delivery success。
- 真实手机/browser、production app 或 PWA prompt/user choice。
- Objective 5 外部 cloud/4G/OSS/CDN/DB/queue proof。

## 4. 剩余风险

材料包仍是现场执行前的软件准备和只读展示，不能替代真实 route/task field run。下一轮若仍没有 O5 外部材料，应继续按 stop rule 避免重复消费 O5 blocker，优先把本轮 material bundle 带到 Objective 2 / Objective 3 的真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success 证据链。
