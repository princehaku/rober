# Sprint 2026.05.16_23-24 Route Task Field Result Reconciliation - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`。目标是把上一轮 result intake、session handoff、execution pack 与八类现场结果材料按同一 `evidence_ref` 做 fail-closed 复账，输出 PC artifact/summary、Robot diagnostics metadata-only summary、mobile/web 只读 panel，并由 Product closeout 保守同步 OKR 与过程日志。

### Task A Autonomy

修改文件：

- `pc-tools/evidence/route_task_field_retest_result_reconciliation.py`
- `pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现结果：

- 新增 dependency-free PC-side `route_task_field_retest_result_reconciliation` gate。
- 支持 artifact、summary、wrapper、nested JSON 输入。
- 输出 `trashbot.route_task_field_retest_result_reconciliation.v1` 与 `trashbot.route_task_field_retest_result_reconciliation_summary.v1`。
- 覆盖八类现场结果材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。
- fail closed 检查 schema/boundary、同一 `evidence_ref`、missing/mismatch、placeholder-only、unsafe copy、弱类型 `same_evidence_ref_required`、success phrasing、`delivery_success=true`、`primary_actions_enabled=true`。

### Task B Robot

修改文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现结果：

- 新增 `route_task_field_retest_result_reconciliation` / `_summary` diagnostics consumer。
- 支持显式 ref、`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION`、`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY`、top-level source、diagnostics summary wrapper。
- 只输出 metadata-only safe summary，不改变 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success 语义。
- 缺失、schema/gate mismatch、缺 ref、same-ref mismatch、非 boolean same-ref、成功措辞、raw/control/ACK/HIL/串口/路径/credential 泄漏均 fail closed。

### Task C Full-stack

修改文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现结果：

- 新增只读“路线任务现场结果复账” panel。
- 消费 `route_task_field_retest_result_reconciliation` / `_summary` 与 Robot diagnostics compatible summary。
- 展示 safe `evidence_ref`、verdict、same evidence ref 状态、八类材料状态、缺失材料、mismatch reasons、operator next steps、safe copy 和证据边界。
- copy/export whitelist-only。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

### Task D Product

修改文件：

- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-done.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/side2side_check.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现结果：

- 补齐本 Epic sprint 后三份 closeout 文档。
- 更新 `OKR.md` 4.1 当前进度快照。
- 更新 `docs/process/okr_progress_log.md` 顶部进度日志。
- 保守记录本轮只小幅推进 Objective 2 / Objective 3 / Objective 4，不提升 Objective 5。

## 2. 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_reconciliation.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py
Ran 6 tests in 0.033s
OK

python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py --help
pass

rg route_task_field_retest_result_reconciliation / boundary strings in pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md
pass

git diff --check -- Task A files
pass
```

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 118 tests in 0.153s
OK

rg route_task_field_retest_result_reconciliation / boundary strings in onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
pass

git diff --check -- Task B files
pass
```

Task C 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 20 tests in 0.044s
OK

node --check mobile/web/app.js
pass

rg route_task_field_retest_result_reconciliation / boundary strings in mobile/web docs/product/mobile_user_flow.md
pass

git diff --check -- Task C files
pass
```

Task D closeout 验证：

```text
rg route_task_field_retest_result_reconciliation / Objective 5 / Objective 2 / Objective 3 / PR #5 / PR #4 / Docker / not_proven / delivery_success=false / primary_actions_enabled=false
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprint closeout files
pass

git diff --cached --check
pass
```

## 3. 偏差与修复

- 本轮没有编辑 Task A/B/C 的产品代码；Product closeout 只编辑允许范围内的 sprint、OKR 和 process log 文件。
- 本轮没有真实现场材料输入，因此 reconciliation gate 通过不等于 field pass。
- 本轮没有运行 broad regression、Docker/Humble colcon build、真实浏览器、真实手机、真实 Nav2、真实电梯、真实 WAVE ROVER/UART/HIL 或外部云验证；验收范围严格限定为 tech-plan 中列出的围栏命令。

## 4. 剩余风险

- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 仍缺真实电梯、真实路线采集、真实 WAVE ROVER/UART/HIL、真实手机/browser 和 Objective 5 external proof。
- PR #4 的 elevator-assisted delivery 主线仍只是 evidence reconciliation 链路推进，未进入受控现场验收。
- PR #5 的硬件基线、2D LiDAR、ToF、vendor/source 风险仍需要真实 SKU/source、采购、安装、接线、供电、标定和 HIL-entry evidence 才能关闭。
