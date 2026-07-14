# Tech Plan - O5 Operator Dropoff Acceptance Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned artifact schema: `trashbot.o5.operator_dropoff_acceptance_gate.v1`
- Planned proof boundary: `software_proof_o5_operator_dropoff_acceptance_gate_only`
- Planned artifact: `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O5，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。
2. 本 sprint 是否针对最低 Objective：是，直接针对 O5。
3. 选择理由：最近 closeout 已明确 terminal-result bridge/reconciliation/live-success-gate、readiness packet、CDN/TLS 4xx、O6/O7 readback/voice draft wrapper 都是 support-only 且不得继续重复消费。本 sprint 选择更接近 Mission Objective 0 的 `operator_dropoff_acceptance` action evidence intake/gate，作为真实 delivery success 的必要输入之一，但不声称真实 delivery success。

## Technical Goal

Robot Software 后续实现一个 fail-closed `operator_dropoff_acceptance` gate，让 O5 可以安全接收 operator/user-action evidence，并把它作为 live-success gate 的必要条件。

合同必须区分两类情况：

- 当前 synthetic/mock fixture：证明 gate schema、脱敏、same-task 校验和 fail-closed 行为存在；固定 `delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`。
- 未来真实/live source：只有 `source_mode=live`、同 task terminal result recorded、live route execution success、`operator_dropoff_acceptance`、HIL pass、safe_to_control 全部满足，才允许 delivery success 被上层 live-success gate 接受。

## Proposed Design

Robot Software 可保守选择具体 API 形态，但必须满足以下产品合同：

1. `DeliveryStateMachine` 增加 `operator_dropoff_acceptance` evidence gate 方法，或新增等价 helper，让 operator/user action 进入同 task delivery evidence 判定。
2. 输入 evidence summary 至少区分：
   - source mode：`synthetic` / `mock` / `live` / `production` 或等价枚举。
   - same-task identity fields：`task_id`、`robot_id`、`packet_id` / `route_intent_id` / `terminal_result_id`。
   - operator action fields：acceptance id、action type、safe actor/source label、occurred_at、safe evidence ref。
   - evidence booleans：terminal result recorded、live route execution success、operator_dropoff_acceptance、HIL pass、safe-to-control。
   - evidence freshness / same-window 约束。
3. 对任何 missing、stale、cross-task、mock-readback-only、unsafe ref、dangerous true fields，输出 fail-closed summary。
4. 对本轮 synthetic/mock fixture，输出：
   - `schema=trashbot.o5.operator_dropoff_acceptance_gate.v1`
   - `proof_boundary=software_proof_o5_operator_dropoff_acceptance_gate_only`
   - `operator_dropoff_acceptance_gate_ready=true`
   - `source_mode=synthetic` 或 `source_mode=mock`
   - `delivery_success=false`
   - `route_execution_success=false`
   - `safe_to_control=false`
   - `hil_pass=false`
   - `delivery_success_accepted=false`
   - `acceptance_decision=blocked_missing_live_success_evidence`
5. Summary 应包含 readable `required_evidence` / `missing_live_evidence` / `next_required_evidence` 字段，方便 Product closeout 和后续 O6/O7 消费方避免误读。

## File Scope For Engineer

Allowed implementation files for `robot-software-engineer` follow-up:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`
- `onboard/scripts/o5_operator_dropoff_acceptance_gate.py`
- `onboard/tests/test_o5_operator_dropoff_acceptance_gate.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/tech-done.md`

Product closeout files after implementation:

- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/side2side_check.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/final.md`

This plan phase does not create closeout docs.

## Interface Impact

- No ROS topic/action/service contract change is required in this plan.
- No hardware, UART, WAVE ROVER, `/cmd_vel`, `/api/base/manual`, or NavigateToPose execution is allowed in this sprint.
- CLI/helper is offline/local and writes a summary artifact only.
- Docs/product must describe that operator dropoff acceptance is necessary evidence, while this run remains `software_proof_o5_operator_dropoff_acceptance_gate_only`.

## Validation Commands For Engineer

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_delivery_state_machine onboard.tests.test_o5_operator_dropoff_acceptance_gate
```

```bash
python3 onboard/scripts/o5_operator_dropoff_acceptance_gate.py --fixture-mode synthetic --output sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json
```

```bash
python3 -m json.tool sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json >/dev/null
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json')
d = json.loads(p.read_text())
assert d['schema'] == 'trashbot.o5.operator_dropoff_acceptance_gate.v1'
assert d['proof_boundary'] == 'software_proof_o5_operator_dropoff_acceptance_gate_only'
assert d['operator_dropoff_acceptance_gate_ready'] is True
assert d['source_mode'] != 'live'
assert d['delivery_success'] is False
assert d['route_execution_success'] is False
assert d['safe_to_control'] is False
assert d['hil_pass'] is False
assert d['acceptance_decision'] == 'blocked_missing_live_success_evidence'
print('operator_dropoff_acceptance_gate_acceptance_ok')
PY
```

```bash
rg -n "operator_dropoff_acceptance|software_proof_o5_operator_dropoff_acceptance_gate_only|delivery_success=false|blocked_missing_live_success_evidence|source_mode=live|safe_to_control" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py onboard/tests/test_o5_operator_dropoff_acceptance_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py onboard/tests/test_o5_operator_dropoff_acceptance_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate
```

## Product Acceptance Checks

Product closeout should reject the sprint if any of these are missing:

- `proof_boundary=software_proof_o5_operator_dropoff_acceptance_gate_only`
- `operator_dropoff_acceptance_gate_ready=true`
- `operator_dropoff_acceptance`
- `source_mode=live` is required only for future positive acceptance, not for current fixture.
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `acceptance_decision=blocked_missing_live_success_evidence`
- Negative tests for missing route execution, terminal result, operator dropoff acceptance, HIL, safe-to-control, source mode live, and same-task identity.
- Docs/product update explaining the boundary.

## Failure Handling

If validation fails, Robot Software must inspect and fix the root cause before closeout. Do not accept the first failed run as final. Typical failure classes:

- synthetic/mock fixture accidentally sets delivery success true;
- operator/user action can pass without live route execution;
- terminal result record is not required;
- HIL or safe-to-control are not required;
- same-task mismatch is not rejected;
- docs/product describes operator confirmation as delivery success.

## Risks And Remaining Evidence

- This sprint does not prove true delivery success.
- This sprint does not prove live route execution, operator/dropoff acceptance, HIL pass, safe-to-control, production cloud, real phone/browser, 4G/SIM, OSS/CDN, or WAVE ROVER UART.
- This sprint should keep O5 percentage flat unless a later closeout adds actual live or production evidence.
- Next scoring move after this gate requires real/live input evidence, not another local wrapper.
