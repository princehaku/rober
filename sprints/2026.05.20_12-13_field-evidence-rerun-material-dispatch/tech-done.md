# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - Tech Done

## 1. Sprint 类型与证据边界

- sprint_type: epic
- closeout 时间：2026-05-20 12:21 Asia/Shanghai
- 本轮抓手：`field_evidence_rerun_material_dispatch`
- 证据边界：`software_proof_docker_field_evidence_rerun_material_dispatch_gate`
- 固定状态：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

本轮只证明 Docker/local software-proof 下的现场证据复跑材料派发包、Robot diagnostics safe alias 和 mobile/web 只读展示已经对齐；不证明真实 route/elevator field pass、真实手机/browser、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL 或 O5 external proof。

## 2. 实际改动

### Task A - Autonomy Algorithm Engineer

- 改动文件：`pc-tools/evidence/field_evidence_rerun_material_dispatch.py`、`tests/test_field_evidence_rerun_material_dispatch.py`、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- 实现内容：新增 `trashbot.field_evidence_rerun_material_dispatch.v1` artifact 和 summary schema，列出 required material groups、owner work orders、rerun commands、callback packet requirements、same safe `evidence_ref`、safe copy 和 fail-closed guards。
- 边界：只读消费兼容 summary，不输出 raw artifact、credential、ROS topic、serial/UART/WAVE ROVER detail、success/control copy 或 true 状态。

### Task B - Robot Platform Engineer

- 改动文件：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- 实现内容：新增 `robot_diagnostics_field_evidence_rerun_material_dispatch_summary` safe alias，兼容 explicit ref、top-level summary、nested summary、status diagnostics 和 diagnostics nested support。
- 边界：fail-closed default；不触发 command、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER 或 HIL。

### Task C - User Touchpoint Full-Stack Engineer

- 改动文件：`mobile/web/app.js`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`、`mobile/web/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- 实现内容：新增只读“现场证据复跑材料派发”panel，优先消费 Robot safe alias 或兼容 summary；展示 owner work orders、required material groups、rerun commands、callback packet requirements、same safe `evidence_ref` 和 fail-closed 状态。
- 边界：不 fetch raw artifact；Start Delivery / Confirm Dropoff / Cancel gating 不变。

### Task D - Product Manager / OKR Owner

- 改动文件：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
- 实现内容：收口本轮 worker 证据，保守更新 OKR 4.1 与进度日志，明确 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。

## 3. 验证结果

Autonomy Task A：

- `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_material_dispatch.py tests/test_field_evidence_rerun_material_dispatch.py`：通过。
- `python3 -m unittest tests.test_field_evidence_rerun_material_dispatch`：`Ran 5 tests in 0.048s OK`。
- `python3 pc-tools/evidence/field_evidence_rerun_material_dispatch.py --help`：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Robot Task B：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 228 tests in 0.665s OK`。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Full-stack Task C：

- `node --check mobile/web/app.js`：通过。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 163 tests ... OK`。
- `python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null`：通过。
- `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null`：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。

Product Task D：

- closeout file existence check：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。

## 4. 偏差与剩余风险

- 无工程实现偏差；本轮按 tech-plan 的 Autonomy / Robot / Full-stack 三 owner 文件范围完成。
- 剩余风险是证据材料本身仍未到位：真实 route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 和真实手机/browser evidence 仍需现场 owner 回填。
- Objective 5 保持约 68%，Objective 1 保持约 81%；本轮不提高 O5/O1，也不把 O2/O3/O4 写成真实现场通过。
