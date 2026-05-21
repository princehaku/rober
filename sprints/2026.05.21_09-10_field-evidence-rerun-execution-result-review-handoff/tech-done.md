# Field Evidence Rerun Execution Result Review Handoff Tech Done

## Sprint Declaration

- sprint_type: epic
- run_time: 2026-05-21 09:22 CST
- capability: `field_evidence_rerun_execution_result_review_handoff`
- evidence_boundary: `software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate`
- required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## Worker 1: Autonomy PC handoff gate

- owner: Autonomy Algorithm Engineer
- changed files:
  - `pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py`
  - `tests/test_field_evidence_rerun_execution_result_review_handoff.py`
  - `pc-tools/README.md`
  - `docs/interfaces/evidence_contracts.md`
  - `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md`

### Actual Changes

- Added canonical schemas `trashbot.field_evidence_rerun_execution_result_review_handoff.v1` and `trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1`.
- The gate consumes `trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1` or the compatible Robot-safe review-decision alias.
- It emits source review decision, safe `evidence_ref`, `owner_handoff`, `blocker_summary`, `next_required_real_materials`, reconciliation guidance, rerun guidance, safe copy, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the evidence boundary.
- The required real materials list remains field-owner backfill only: same-safe-`evidence_ref` task record, route/elevator runtime logs, route completion signal, elevator door/floor evidence, human assistance note, dropoff or cancel completion, delivery result, diagnostics/mobile safe summary, and true phone/browser evidence.
- Updated PC evidence docs and focused tests for the new handoff contract.

### Verification Results

- `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py`
  - Result: passed.
- `python3 -m unittest tests.test_field_evidence_rerun_execution_result_review_handoff`
  - Result: passed, `Ran 5 tests ... OK`.
- `python3 pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py --help`
  - Result: passed.
- `rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|owner_handoff|next_required_real_materials|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed; matches include the new PC gate, tests, docs, and sprint notes.
- `git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py tests/test_field_evidence_rerun_execution_result_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed with no output.

### Remaining Risk

- This is `software_proof` only. It does not prove real field rerun, real task record, real Nav2/fixed-route runtime, real route/elevator field pass, real phone/browser behavior, WAVE ROVER/UART/HIL, dropoff/cancel completion, delivery result, or delivery success.

## Worker 2: Robot diagnostics safe alias

- owner: Robot Platform Engineer
- changed files:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_runtime_contracts.md`
  - `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md`

### Actual Changes

- Added `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary` to `operator_gateway_diagnostics.py`.
- The alias consumes only canonical `trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1` material, prefers the Robot-safe summary, and blocks raw review-decision/result packet inputs.
- The Robot-visible output is limited to source review decision, safe `evidence_ref`, owner handoff, blocker summary, `next_required_real_materials`, reconciliation/rerun guidance, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the evidence boundary.
- Added focused unit coverage for canonical summary consumption, payload alias compatibility, raw-only rejection, unsupported boundary, same-ref mismatch, unsafe material blocking, and forbidden string omission.
- Updated `docs/interfaces/ros_runtime_contracts.md` with the new safe alias contract and non-exposure boundary.

### Verification Results

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Result: passed with no output.
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Result: passed, `Ran 253 tests in 0.899s`, `OK`.
- `rg -n "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary|field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed; matches include the new diagnostics alias, schema, evidence boundary, tests, interface docs, and sprint notes.
- `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed with no output.

### Remaining Risk

- This is `software_proof` only. It does not prove real field rerun, real Nav2/fixed-route runtime, real route/elevator field pass, real phone/browser behavior, WAVE ROVER/UART/HIL, dropoff/cancel completion, delivery result, or delivery success.
- No ROS topic/action/service/launch/control semantics were changed.

## Worker 3: Mobile/web read-only panel

- owner: User Touchpoint Full-Stack Engineer
- changed files:
  - `mobile/web/app.js`
  - `mobile/web/fixtures/status.json`
  - `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_handoff.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
  - `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md`

### Actual Changes

- Added the read-only mobile/web "现场证据复跑执行结果复核交接" panel.
- The panel prefers `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary`, then falls back only to compatible safe summary fields in existing status/readiness/diagnostics shapes.
- The panel shows source review decision, safe `evidence_ref`, owner handoff, blocker summary, `next_required_real_materials`, reconciliation guidance, rerun guidance, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Added status and dedicated Robot diagnostics fixtures for the safe handoff summary.
- Added mobile unittest coverage for fail-closed rendering, safe fixture content, unchanged Start Delivery / Confirm Dropoff / Cancel gating, and forbidden raw/control text.
- Updated `docs/product/mobile_user_flow.md` with the new panel contract and software-proof boundary.

### Verification Results

- `node --check mobile/web/app.js`
  - Result: passed with no output.
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`
  - Result: passed, `Ran 203 tests OK`.
- `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null`
  - Result: passed with no output.
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_handoff.json >/dev/null`
  - Result: passed with no output.
- `rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场证据复跑执行结果复核交接" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed; matches include the new panel, fixtures, tests, product doc, and sprint notes.
- `git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
  - Result: passed with no output.

### Remaining Risk

- This is Docker/local mobile `software_proof` only. It does not prove real phone/browser behavior, real route/elevator field pass, dropoff/cancel completion, delivery result, delivery success, HIL, Objective 5 external proof, PR #5 hardware proof, or PR #6 runtime proof.
- Live display still depends on Robot diagnostics publishing the safe alias in `/api/status` or `/api/diagnostics`.

## Product Closeout Notes

- Product closeout merged the three worker records because parallel writes left `tech-done.md` with only Worker 2/3 before closeout.
- Product reviewed the worker-reported docs sync: `docs/interfaces/evidence_contracts.md`, `docs/interfaces/ros_runtime_contracts.md`, `pc-tools/README.md`, and `docs/product/mobile_user_flow.md` were updated by responsible workers.
- Product keeps Objective 5 at about 68% and Objective 1 at about 81%; no real O5 external materials, O1 hardware/HIL materials, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, or PR #6 runtime proof appeared.
- Product keeps Objective 2/3/4 at about 99%; this sprint improves handoff/readability only and does not close real field, route/elevator, or phone/browser proof gaps.
