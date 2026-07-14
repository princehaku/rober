# Tech Done - O5 Operator Dropoff Acceptance Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/`
- Implementation owner: `robot-software-engineer`
- Artifact schema: `trashbot.o5.operator_dropoff_acceptance_gate.v1`
- Proof boundary: `software_proof_o5_operator_dropoff_acceptance_gate_only`
- Current artifact: `artifacts/operator_dropoff_acceptance_gate_summary.json`
- Completion time: 2026-07-14 07:44 CST

## Actual Changes

- `DeliveryStateMachine` now has `operator_dropoff_acceptance_gate(...)`, with schema `trashbot.o5.operator_dropoff_acceptance_gate.v1`.
- The gate accepts future positive input only when all required live evidence is present: `source_mode=live`, same-task identity, same-task terminal result recorded, live route execution success, same-task `operator_dropoff_acceptance`, HIL pass, `safe_to_control=true`, same-window freshness, and a sanitized basename evidence ref.
- The gate output is compatible with `delivery_state_live_success_gate(...)`, but it still keeps `delivery_success=false`; operator/user action is a necessary input, not a sufficient delivery success decision.
- Non-live source modes, missing evidence, identity mismatch, stale evidence, unsafe evidence refs, and non-live dangerous true fields fail closed with `acceptance_decision=blocked_missing_live_success_evidence`.
- Added `onboard/scripts/o5_operator_dropoff_acceptance_gate.py` with `--fixture-mode synthetic` only. The CLI writes the sprint artifact and cannot be used as a live capture path.
- Added state-machine and CLI tests covering future live-complete acceptance, live-success gate consumption, synthetic fail-closed fixture, missing route execution, missing terminal result, missing operator acceptance, missing HIL, missing safe-to-control, identity mismatch, stale evidence, unsafe evidence ref, and non-live dangerous true fields.
- Updated product docs to state that operator dropoff acceptance is a required evidence entry, not delivery success.

## Artifact Result

`artifacts/operator_dropoff_acceptance_gate_summary.json` was generated from the synthetic fixture and fixed to:

- `source_mode=synthetic`
- `operator_dropoff_acceptance_gate_ready=true`
- `operator_dropoff_acceptance_gate_accepted=false`
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `acceptance_decision=blocked_missing_live_success_evidence`

## Validation Results

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py
```

Result: passed with no output.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_delivery_state_machine onboard.tests.test_o5_operator_dropoff_acceptance_gate
```

First run failed with 3 targeted failures: nested `route_execution.success=false`, `terminal_result.recorded=false`, or `hil.pass=false` could still pass because top-level booleans stayed true. Fixed by requiring both the top-level live signal and the same-task section signal for route execution, terminal result, and HIL. Re-run result:

```text
Ran 27 tests in 0.004s
OK
```

```bash
python3 onboard/scripts/o5_operator_dropoff_acceptance_gate.py --fixture-mode synthetic --output sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json
```

Result: passed and printed JSON with `schema=trashbot.o5.operator_dropoff_acceptance_gate.v1`, `proof_boundary=software_proof_o5_operator_dropoff_acceptance_gate_only`, and `acceptance_decision=blocked_missing_live_success_evidence`.

```bash
python3 -m json.tool sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json >/dev/null
```

Result: passed with no output.

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

Result: `operator_dropoff_acceptance_gate_acceptance_ok`.

```bash
rg -n "operator_dropoff_acceptance|software_proof_o5_operator_dropoff_acceptance_gate_only|delivery_success=false|blocked_missing_live_success_evidence|source_mode=live|safe_to_control" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py onboard/tests/test_o5_operator_dropoff_acceptance_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate
```

Result: passed, anchors found across code, tests, docs, plan docs, and generated artifact.

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_state_machine.py onboard/src/ros2_trashbot_behavior/test/test_delivery_state_machine.py onboard/scripts/o5_operator_dropoff_acceptance_gate.py onboard/tests/test_o5_operator_dropoff_acceptance_gate.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate
```

Result: passed with no output.

## Remaining Risks

- This sprint does not prove true delivery success.
- This sprint does not prove live route execution, real operator/dropoff action, HIL pass, safe-to-control, production cloud, 4G/SIM, OSS/CDN live traffic, or true phone/browser proof.
- The current artifact is synthetic and must keep O5 flat unless Product closeout later consumes actual live/production evidence.

## Coordination

- Product: needed for side2side/final acceptance and OKR flat closeout wording.
- Hardware: not needed in this sprint; future positive acceptance needs HIL pass and `safe_to_control=true`.
- Autonomy: not needed in this sprint; future positive acceptance needs live route execution success.
- Full-Stack: not needed in this sprint; future phone/browser UI should render this gate as necessary evidence only, not delivery success.
