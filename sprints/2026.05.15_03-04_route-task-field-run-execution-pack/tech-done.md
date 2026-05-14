# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - Tech Done

sprint_type: epic

## 1. 实际改动

Task A `autonomy-engineer` 完成 `software_proof_docker_route_task_field_run_execution_pack_gate` 的 PC/evidence 执行包：

- 新增 `pc-tools/evidence/route_task_field_run_execution_pack.py` 和 `pc-tools/evidence/test_route_task_field_run_execution_pack.py`。
- 更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
- 输出 `schema=trashbot.route_task_field_run_execution_pack.v1`、`evidence_boundary=software_proof_docker_route_task_field_run_execution_pack_gate`、`same_evidence_ref_required=true`、现场材料模板、first-run/rerun commands、phone-safe summary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 首轮 unsupported schema 误判已由 Task A 修复并复验。

Task B `robot-software-engineer` 完成 Robot diagnostics metadata-only consumption：

- 更新 `operator_gateway_diagnostics.py`、`test_operator_gateway_diagnostics.py` 和 `docs/interfaces/ros_contracts.md`。
- 新增 `route_task_field_run_execution_pack` / `route_task_field_run_execution_pack_summary` metadata-only summary。
- 支持 explicit ref 和 `TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK`。
- 保持 collect/dropoff/cancel、ACK、cursor、terminal ACK、Nav2、HIL、dropoff/cancel completion、delivery success 隔离。

Task C `full-stack-software-engineer` 完成手机只读触点：

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`test_mobile_web_entrypoint.py` 和 `docs/product/mobile_user_flow.md`。
- 新增只读“路线任务现场执行包”panel，消费 status、phone_readiness、diagnostics 和 nested summary 中的 `route_task_field_run_execution_pack*`。
- 缺 summary 时显示 blocked/not_proven，不 fetch raw artifact，不读取本机路径，不改变 Start/Confirm/Cancel gating。

Task D `product-okr-owner` 完成本 closeout：

- 新增本文件、`side2side_check.md` 和 `final.md`。
- 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，把 Objective 2 / Objective 3 仅从约 62% 保守上调到约 63%。
- Objective 5 保持约 66%，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料。

## 2. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_execution_pack.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_execution_pack.py
Ran 6 tests OK

python3 pc-tools/evidence/route_task_field_run_execution_pack.py --help
pass

required rg
pass

git diff --check -- Task A files
pass
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
Ran 61 tests OK

required rg
pass

git diff --check -- Task B files
pass
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
Ran 12 tests OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- Task C files
pass
```

Task D 验证：

```text
rg closeout/OKR/process/sprint boundary check
pass; key hits include sprint name, software proof boundary, Objective 2, Objective 3, Objective 5, not_proven, delivery success and HIL

git diff --check -- OKR.md docs/process/okr_progress_log.md tech-done.md side2side_check.md final.md
pass
```

## 3. 偏差和失败定位

- Task A 首轮把 unsupported schema 误判为其他状态，已修复并复验通过。
- 本轮没有执行真实 Nav2/fixed-route、真实路线采集、真实串口/UART、WAVE ROVER 或 HIL 验证；这是本 sprint 的明确边界，不是实现遗漏。
- 本轮没有生产公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据；Objective 5 不上调。

## 4. 剩余风险

- `software_proof_docker_route_task_field_run_execution_pack_gate` 只证明 execution pack、diagnostics summary 和 mobile read-only panel 在 Docker/local 软件环境可生成、可消费、可安全展示。
- Execution pack ready 不等于真实 Nav2/fixed-route，不等于真实路线采集，不等于同一 `evidence_ref` 上车复账，不等于 dropoff/cancel completion，不等于 delivery success。
- 下一步 O2/O3 真正增量应来自现场材料：route status、Nav2/fixed-route runtime log、task record、robot-side task evidence、support-safe mobile summary 和上一轮 review console 在同一 `evidence_ref` 下的真实采集与复账。
