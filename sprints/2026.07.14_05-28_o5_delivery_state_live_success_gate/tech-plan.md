# Tech Plan - O5 Delivery State Live Success Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `Robot Software`
- Planned artifact schema: `trashbot.o5.delivery_state_live_success_gate.v1`
- Planned proof boundary: `software_proof_o5_delivery_state_live_success_gate_only`
- Planned artifact: `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O5，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。
2. 本 sprint 是否针对最低 Objective：是，直接针对 O5。
3. 选择理由：最近 O5/O6/O7 closeout 已反复说明 CDN/TLS 4xx probe、readiness packet、cloud external review-decision、bounded route terminal-result bridge、terminal-result intake/export、mission bundle export、delivery state terminal reconciliation 都是 support-only。本轮不重复 wrapper/export/readback，而是把 O5 状态机未来接受 live delivery success 的完整证据门槛固化到 `DeliveryStateMachine`。

## Technical Goal

Robot Software 增加 `delivery_state_live_success_gate` 合同，让 `DeliveryStateMachine` 对 delivery success 采用严格 fail-closed 语义。

合同必须区分两类情况：

- 当前 synthetic/current-live-shaped 验证：证明 gate 合同已存在，但固定 `current_live_evidence_observed=false`、`delivery_success_claimed_by_this_run=false`、`real_world_delivery_proven=false`、`safe_to_control=false`、`hil_pass=false`。
- 未来真实/live source：只有完整 live route execution、operator/dropoff acceptance、HIL pass、safe-to-control、same-task identity、terminal result record 同时满足，才允许 `delivery_success_accepted_for_state_machine=true`。

## Proposed Design

Robot Software 可保守选择具体 API 形态，但必须满足以下产品合同：

1. `DeliveryStateMachine` 增加一个 live success evidence gate 方法或等价状态转移入口。
2. 输入 evidence summary 至少区分：
   - source mode：`synthetic-current-live` / `mock` / `live` / `production` 或等价枚举。
   - same-task identity fields：`task_id`、`robot_id`、`packet_id` / `route_intent_id` / terminal result id。
   - evidence booleans：live route execution, operator/dropoff acceptance, HIL pass, safe-to-control, terminal result record。
   - evidence freshness / same-window 约束。
3. 对任何 missing、stale、cross-task、mock-readback-only、dangerous true fields，输出 fail-closed summary。
4. 对本轮 synthetic fixture，输出：
   - `schema=trashbot.o5.delivery_state_live_success_gate.v1`
   - `proof_boundary=software_proof_o5_delivery_state_live_success_gate_only`
   - `live_success_gate_contract_ready=true`
   - `current_live_evidence_observed=false`
   - `delivery_success_claimed_by_this_run=false`
   - `real_world_delivery_proven=false`
   - `safe_to_control=false`
   - `hil_pass=false`
   - `delivery_success_accepted_for_state_machine=false`
5. Summary 应包含 readable `required_evidence` / `missing_live_evidence` / `acceptance_decision` 字段，方便 Product closeout 和后续 O6/O7 消费方避免误读。

## File Scope For Engineer

Allowed implementation files for `Robot Software` follow-up:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py`
- `onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`
- `onboard/scripts/o5_delivery_state_live_success_gate.py`
- `onboard/tests/test_o5_delivery_state_live_success_gate.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/tech-done.md`

Product closeout files after implementation:

- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/side2side_check.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/final.md`

This plan phase does not create closeout docs.

## Interface Impact

- No ROS topic/action/service contract change is required.
- No hardware, UART, WAVE ROVER, `/cmd_vel`, `/api/base/manual`, or NavigateToPose execution is allowed in this sprint.
- CLI is offline/local and writes a summary artifact only.
- Docs/product must describe that live success is accepted only after complete live evidence, while this run is `software_proof_o5_delivery_state_live_success_gate_only`.

## Validation Commands For Engineer

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/scripts/o5_delivery_state_live_success_gate.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_delivery_state_machine onboard.tests.test_o5_delivery_state_live_success_gate
```

```bash
python3 onboard/scripts/o5_delivery_state_live_success_gate.py --fixture-mode synthetic-current-live --output sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json
```

```bash
python3 -m json.tool sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json >/dev/null
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json')
d = json.loads(p.read_text())
assert d['schema'] == 'trashbot.o5.delivery_state_live_success_gate.v1'
assert d['proof_boundary'] == 'software_proof_o5_delivery_state_live_success_gate_only'
assert d['live_success_gate_contract_ready'] is True
assert d['current_live_evidence_observed'] is False
assert d['delivery_success_claimed_by_this_run'] is False
assert d['real_world_delivery_proven'] is False
assert d['safe_to_control'] is False
assert d['hil_pass'] is False
print('delivery_state_live_success_gate_acceptance_ok')
PY
```

```bash
rg -n "delivery_state_live_success_gate|software_proof_o5_delivery_state_live_success_gate_only|live_success_gate_contract_ready|current_live_evidence_observed=false|delivery_success_claimed_by_this_run=false|real_world_delivery_proven=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_live_success_gate.py onboard/tests/test_o5_delivery_state_live_success_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_delivery_state_live_success_gate.py onboard/tests/test_o5_delivery_state_live_success_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate
```

## Product Acceptance Checks

Product closeout should reject the sprint if any of these are missing:

- `proof_boundary=software_proof_o5_delivery_state_live_success_gate_only`
- `live_success_gate_contract_ready=true`
- `current_live_evidence_observed=false`
- `delivery_success_claimed_by_this_run=false`
- `real_world_delivery_proven=false`
- `safe_to_control=false`
- `hil_pass=false`
- Negative tests for missing live route execution, operator/dropoff acceptance, HIL, safe-to-control, terminal result, and same-task identity.
- Docs/product update explaining the boundary.

## Failure Handling

If validation fails, Robot Software must inspect and fix the root cause before closeout. Do not accept the first failed run as final. Typical failure classes:

- synthetic fixture accidentally sets delivery success true;
- unsafe source mode can pass the gate;
- same-task mismatch is not rejected;
- terminal result record is not required;
- docs/product still describes this as delivery success.

## Risks And Remaining Evidence

- This sprint does not prove true delivery success.
- This sprint does not prove live route execution, operator/dropoff acceptance, HIL pass, safe-to-control, production cloud, real phone/browser, 4G/SIM, OSS/CDN, or WAVE ROVER UART.
- This sprint should keep O5 percentage flat unless a later closeout adds actual live or production evidence.
- Next scoring move after this contract requires real/live input evidence, not another local wrapper.
