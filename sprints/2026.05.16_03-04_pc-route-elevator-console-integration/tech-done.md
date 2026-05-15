# Sprint 2026.05.16_03-04 PC Route Elevator Console Integration - Tech Done

sprint_type: epic

## Task A - Autonomy Algorithm Engineer

### 自主能力目标和本轮抓手

- 目标：把 PC route debug console 从 route progress + recent task 扩展为 route/elevator reconciliation 同屏复盘入口。
- 抓手：新增可选 `--elevator-route-reconciliation` 输入，在同一 `trashbot.pc_route_debug_console.v1` HTML/API summary 中输出 `route_elevator_reconciliation` 白名单摘要。

### 实际改动

- `pc-tools/route/route_debug_web.py`：保留父级 `software_proof_docker_pc_route_debug_console_gate`，新增嵌套 `route_elevator_reconciliation.evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`、`--elevator-route-reconciliation` CLI 参数、HTML “Elevator Route Reconciliation” section，以及 artifact/summary schema、boundary、source、success/control/unsafe copy 围栏。
- `pc-tools/route/test_route_debug_web.py`：新增 elevator-route reconciliation artifact 接入、HTTP API 透出、unsupported schema、unsafe copy、success claim blocked 测试。
- `pc-tools/route/README.md`、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`：同步记录 CLI 用法、summary 字段、证据边界与 not_proven 范围。

### 接口影响

- `build_console_summary()` 与 `make_handler()` 新增可选参数 `elevator_route_reconciliation`；未提供时仍返回 `route_elevator_reconciliation.lookup_status=not_provided`，不影响原 route/task 摘要读取。
- JSON/API 新增 `route_elevator_reconciliation` 字段；父级 `evidence_boundary` 保持 `software_proof_docker_pc_route_debug_console_gate`，嵌套字段包含 `evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate` 与 `source_evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`，其余只包含 safe `evidence_ref`、status/verdict、same-evidence-ref 状态、source states、materials status、operator next steps、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/route/route_debug_web.py pc-tools/route/test_route_debug_web.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/route/test_route_debug_web.py`：通过，`Ran 7 tests in 0.533s OK`。
- `python3 pc-tools/route/route_debug_web.py --help`：通过，输出包含 `--elevator-route-reconciliation`。
- `rg -n "route_elevator_reconciliation|software_proof_docker_pc_route_elevator_console_integration_gate|elevator-route-reconciliation|delivery_success=false|not_proven" pc-tools/route pc-tools/README.md docs/navigation/fixed_route_workflow.md`：通过。
- `git diff --check -- pc-tools/route/route_debug_web.py pc-tools/route/test_route_debug_web.py pc-tools/route/README.md pc-tools/README.md docs/navigation/fixed_route_workflow.md`：通过。

### 数据、样本或调试输出变化

- 测试 fixture 新增 `trashbot.elevator_route_evidence_reconciliation.v1` artifact 与 `trashbot.elevator_route_evidence_reconciliation_summary.v1` phone-safe summary 样例。
- HTML/API summary 新增 read-only `route_elevator_reconciliation` 调试输出；缺失或不安全输入会保留 blocked/not_proven 摘要。
- 集成评审修正：父级 PC console boundary 已恢复为 `software_proof_docker_pc_route_debug_console_gate`；新增 gate 只放在嵌套 `route_elevator_reconciliation.evidence_boundary`。

### 剩余风险

- 当前父级仍是 `software_proof_docker_pc_route_debug_console_gate`，嵌套集成才是 `software_proof_docker_pc_route_elevator_console_integration_gate`；两者都只完成 Docker/local software proof，不证明真实 Nav2/fixed-route、真实路线采集、真实电梯、WAVE ROVER/UART/HIL、dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- 与 Robot diagnostics、mobile/web 的并行集成需以各自 worker 验证为准；本 Task A 没有修改其文件范围。

## Task C - User Touchpoint Full-Stack Engineer

### 实际改动

- `mobile/web/app.js`：PC 路线调试 Console 面板新增 `route_elevator_reconciliation` 嵌套摘要展示，字段只来自 `pc_route_debug_console.route_elevator_reconciliation`，展示 verdict、safe evidence ref、missing、mismatch、`delivery_success=false`、`primary_actions_enabled=false`、source boundary、integration boundary 和 `not_proven`；缺字段时保持 `blocked/not_proven`，不读取 raw artifact，不改变 Start / Confirm Dropoff / Cancel gating。
- `mobile/fixtures/mobile_web_status.fixture.json`：在 `pc_route_debug_console` 内加入 phone-safe `route_elevator_reconciliation` fixture，固定 `software_proof_docker_pc_route_elevator_console_integration_gate`、`delivery_success=false`、`primary_actions_enabled=false` 和真实现场缺口。
- `mobile/test_mobile_web_entrypoint.py`：新增 Task C fence 测试，覆盖 nested field、边界、fixture、fail-closed 与 unsafe 字段排除。
- `docs/product/mobile_user_flow.md`：补充 PC console panel 读取嵌套电梯路线复账摘要的用户流程和证据边界说明。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py`：通过，`Ran 46 tests in 0.144s OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py`：通过。
- `node --check mobile/web/app.js`：通过。
- `rg -n "route_elevator_reconciliation|software_proof_docker_pc_route_elevator_console_integration_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md`：通过，命中新 panel、fixture、测试和文档边界。
- `git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md`：通过。

### 剩余风险

- 当前仍是 `software_proof_docker_pc_route_elevator_console_integration_gate`，不证明真实 PC 现场 console、真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## Task B - Robot Platform Engineer

### 实际改动

- `operator_gateway_diagnostics.py`：`pc_route_debug_console` 新增 `route_elevator_reconciliation` 嵌套 metadata-only summary；父级 `evidence_boundary` 保持 `software_proof_docker_pc_route_debug_console_gate`，嵌套 summary 使用 `software_proof_docker_pc_route_elevator_console_integration_gate`。
- `operator_gateway_diagnostics.py`：嵌套 summary 只白名单保留 availability、reconciliation status、elevator assist status、route completion status、operator next steps、`not_proven` 和 safe copy；控制、ACK、Nav2、HIL、dropoff/cancel completion、delivery success 全部 fail-closed。
- `test_operator_gateway_diagnostics.py`：覆盖可用嵌套 summary、未配置默认 blocked、以及带成功/控制布尔的不安全嵌套来源。
- `docs/interfaces/ros_contracts.md`：同步说明父级/嵌套 evidence boundary 和 fail-closed 字段边界。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，`Ran 81 tests in 0.076s OK`。
- `rg -n "route_elevator_reconciliation|pc_route_debug_console|software_proof_docker_pc_route_elevator_console_integration_gate|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md`：通过，命中新嵌套 summary、PC console 边界、嵌套 gate 和 fail-closed 字段。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md`：通过。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.16_03-04_pc-route-elevator-console-integration/tech-done.md`：通过。

### 剩余风险

- 当前边界是 `software_proof_docker_pc_route_elevator_console_integration_gate`；未覆盖真实 Nav2、真实电梯运行、WAVE ROVER、串口/HIL、远端 ACK 或真实交付成功。

## Product Closeout - Product Manager / OKR Owner

### 实际改动

- `side2side_check.md`：新增本轮用户价值、OKR 映射、KR 拆解、责任 Engineer、side-by-side 验收和证据链缺口。
- `final.md`：新增 sprint 收口结论、实际改动、工程验证结果、OKR 更新和下一步风险。
- `OKR.md`：更新 4.1 当前快照与第 6 节；Objective 3 从约 74% 保守上调到约 75%，Objective 2/O4 仅记支撑不重复上调，Objective 5 保持约 66%，Objective 1 不上调。
- `docs/process/okr_progress_log.md`：顶部追加本 sprint 证据、验证结果、OKR 变动和 `not real` 边界。

### 验收结果

- Product closeout 指定 `rg`：通过，命中 `pc_route_elevator_console`、`route_elevator_reconciliation`、`software_proof_docker_pc_route_elevator_console_integration_gate`、`Objective 3`、`Objective 5`、`not real`、`不证明` 和 `delivery_success=false`。
- Product closeout scoped `git diff --check`：通过。

### 剩余风险

- 本轮仍是 `software_proof_docker_pc_route_elevator_console_integration_gate`，not real Nav2/fixed-route proof, not real elevator proof, not WAVE ROVER/UART/HIL proof, not real phone/browser proof, not dropoff/cancel completion, not delivery success, and not O5 external proof。
