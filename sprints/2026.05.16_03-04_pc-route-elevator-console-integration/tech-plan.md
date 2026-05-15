# Sprint 2026.05.16_03-04 PC Route Elevator Console Integration - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `software_proof_docker_pc_route_elevator_console_integration_gate`。复用现有 PC route debug console schema `trashbot.pc_route_debug_console.v1`，在其 summary 内增加 `route_elevator_reconciliation` 白名单字段，并同步 Robot diagnostics 与 mobile PC console panel 的 metadata-only 展示。

新增字段只接受上一轮 `trashbot.elevator_route_evidence_reconciliation.v1` / `trashbot.elevator_route_evidence_reconciliation_summary.v1`，必须保持：

- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`
- PC console 顶层仍为 `software_proof_docker_pc_route_debug_console_gate`

## 2. 任务拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/route/route_debug_web.py`
- `pc-tools/route/test_route_debug_web.py`
- `pc-tools/route/README.md`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现：

- `route_debug_web.py` 新增可选参数 `--elevator-route-reconciliation`。
- `build_console_summary()` 读取复账 JSON，产出 `route_elevator_reconciliation` safe summary；缺失/坏 JSON/unsupported schema/boundary/success claim/unsafe copy 均 blocked。
- HTML 增加只读 “Elevator Route Reconciliation” section。
- 输出 `safe_copy` / `safe_phone_copy` 明确 `not delivery success`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/route/route_debug_web.py pc-tools/route/test_route_debug_web.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/route/test_route_debug_web.py
python3 pc-tools/route/route_debug_web.py --help
rg -n "route_elevator_reconciliation|software_proof_docker_pc_route_elevator_console_integration_gate|elevator-route-reconciliation|delivery_success=false|not_proven" pc-tools/route pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/route/route_debug_web.py pc-tools/route/test_route_debug_web.py pc-tools/route/README.md pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现：

- `summarize_pc_route_debug_console()` 保留 `route_elevator_reconciliation` metadata-only summary。
- 该字段仍走 `_safe_pc_route_debug_dict()` 脱敏截断，不接受控制、ACK、Nav2、HIL、success claim。
- 文档说明 PC console 可携带该 nested summary，但不改变 command/status/ACK envelope。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_elevator_reconciliation|pc_route_debug_console|software_proof_docker_pc_route_elevator_console_integration_gate|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现：

- Mobile PC route debug panel 从 `pc_route_debug_console.route_elevator_reconciliation` 读取并展示复账 status/verdict、safe evidence ref、missing/mismatch、boundary 和 not_proven。
- 缺 nested summary 时保持 blocked/not_proven。
- 不 fetch raw artifact，不改变 Start / Confirm Dropoff / Cancel gating。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_elevator_reconciliation|software_proof_docker_pc_route_elevator_console_integration_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对该最低 Objective：否。
3. 理由：Objective 5 当前下一步需要真实外部公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据；本机只有 Docker，继续堆本地 O5 metadata 会重复消费同一 blocker。Objective 1 也需要真实 WAVE ROVER/UART/HIL，当前不可得。最低可行动目标是 Objective 3，且最近 final 的具体缺口是把 PC route debug、task record、route completion signal 与 elevator reconciliation 放到同一复盘入口。

## 4. 风险边界

- 本轮只证明 PC/local/Docker route debug console 可读可消费该复账摘要。
- 不证明真实路线采集、真实 Nav2/fixed-route、真实电梯、真实手机/browser、WAVE ROVER/UART/HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 所有新增文案必须保持 read-only、not_proven 和 `delivery_success=false`。

## 5. Product 收口命令

```bash
rg -n "pc_route_elevator_console|route_elevator_reconciliation|software_proof_docker_pc_route_elevator_console_integration_gate|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_03-04_pc-route-elevator-console-integration OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_03-04_pc-route-elevator-console-integration OKR.md docs/process/okr_progress_log.md
```
