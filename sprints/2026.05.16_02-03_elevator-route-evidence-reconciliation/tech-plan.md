# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `software_proof_docker_elevator_route_evidence_reconciliation_gate`，把 elevator rehearsal evidence 与 route task completion signal 做同一 `evidence_ref` 复账。复用现有 PC artifact -> Robot diagnostics metadata-only -> `mobile/web` 只读 panel 模式。

核心 contract：

- Artifact schema：`trashbot.elevator_route_evidence_reconciliation.v1`。
- Summary schema：`trashbot.elevator_route_evidence_reconciliation_summary.v1`。
- Evidence boundary：`software_proof_docker_elevator_route_evidence_reconciliation_gate`。
- 必填边界：`source=software_proof`、`same_evidence_ref_required=true`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 包含真实电梯、真实 Nav2/fixed-route、HIL、dropoff/cancel completion、delivery success、O5 external proof。

## 2. 任务拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/elevator_route_evidence_reconciliation.py`
- `pc-tools/evidence/test_elevator_route_evidence_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/elevator_assisted_delivery.md`

实现：

- 新增 dependency-free CLI，支持 `--elevator-json`、`--route-completion-json`、`--output`、`--evidence-ref`、`--once-json`。
- 支持输入 `trashbot.elevator_assist_rehearsal_evidence.v1` / summary 和 `trashbot.route_task_completion_signal.v1` / summary。
- 输出 `reconciliation_verdict`、`same_evidence_ref_status`、source states、missing/mismatch、operator next steps、phone-safe summary。
- fail closed：缺文件、坏 JSON、unsupported schema/boundary、evidence_ref mismatch、unsafe copy、success/control claim。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/elevator_route_evidence_reconciliation.py pc-tools/evidence/test_elevator_route_evidence_reconciliation.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_route_evidence_reconciliation.py
python3 pc-tools/evidence/elevator_route_evidence_reconciliation.py --help
rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md docs/product/elevator_assisted_delivery.md
git diff --check -- pc-tools/evidence/elevator_route_evidence_reconciliation.py pc-tools/evidence/test_elevator_route_evidence_reconciliation.py pc-tools/README.md docs/navigation/fixed_route_workflow.md docs/product/elevator_assisted_delivery.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现：

- Diagnostics 新增 `elevator_route_evidence_reconciliation` / summary metadata-only consumption。
- 支持 explicit ref 与环境变量 `TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION` / `_SUMMARY`。
- 严格校验 schema、boundary、safe summary、`delivery_success=false`、`primary_actions_enabled=false`。
- 不触发 collect/dropoff/cancel、remote ACK、terminal ACK、Nav2、HIL 或 delivery success claim。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现：

- `mobile/web` 新增只读“电梯路线证据复账” panel。
- 展示 safe `evidence_ref`、same evidence ref 状态、source states、missing/mismatch、operator next steps、not_proven、boundary。
- 缺 summary 时 fail closed；命中 raw artifact、本机路径、ROS topic、serial/UART、WAVE ROVER、凭证、success wording 时降级为 safe copy。
- 不改变 Start / Confirm Dropoff / Cancel gating。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 是否针对该最低 Objective：否。
3. 理由：Objective 5 当前下一步需要真实外部公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据；本机只有 Docker，继续堆本地 O5 metadata 会重复消费同一 blocker。Objective 3 是最低可行动作，且最近 final / PRD 反复要求把电梯阶段证据、Nav2/fixed-route runtime、task record 和 completion signal 放到同一 `evidence_ref` 复账链。

## 4. 风险边界

- 本轮不涉及硬件参数、UART、WAVE ROVER 或 Orange Pi，不能作为 Objective 1 HIL 证据。
- 本轮不访问真实 ROS graph、Nav2 runtime、真实电梯、真实手机、外部云、OSS/CDN、DB/queue 或 4G。
- 所有可见文案必须保持 `delivery_success=false` 和 `not_proven`；ACK、summary、reconciliation verdict 都不能写成真实完成。

## 5. Product 收口命令

```bash
rg -n "elevator_route_evidence_reconciliation|software_proof_docker_elevator_route_evidence_reconciliation_gate|Objective 3|Objective 5|not real|不证明|delivery_success=false" sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_02-03_elevator-route-evidence-reconciliation OKR.md docs/process/okr_progress_log.md
```
