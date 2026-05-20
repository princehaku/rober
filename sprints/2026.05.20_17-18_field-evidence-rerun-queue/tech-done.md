# Field Evidence Rerun Queue Tech Done

## Robot Platform Engineer Update

- Updated at: 2026-05-20 17:18:28 CST
- Scope: Robot diagnostics safe alias only; no Product closeout, PC gate, mobile panel, hardware config, or OKR update was changed.
- Changed files:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_runtime_contracts.md`
  - `sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-done.md`

### Actual Implementation

- Added `robot_diagnostics_field_evidence_rerun_queue_summary` and matching `field_evidence_rerun_queue` / `field_evidence_rerun_queue_summary` diagnostics payload aliases.
- Added fail-closed summary support for `trashbot.field_evidence_rerun_queue_summary.v1`, with `source_schema=trashbot.field_evidence_rerun_queue.v1` and `evidence_boundary=software_proof_docker_field_evidence_rerun_queue_gate`.
- Preserved `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Consumed only safe direct or nested summary metadata, and blocked missing summary, unsupported schema or boundary, `safe_evidence_ref` mismatch, missing required safe metadata, unsafe fields, enabled actions, raw artifact markers, local paths, checksums, tracebacks, hardware transport details, HIL/pass wording, and delivery/control claims.
- Scrubbed `latest_status` raw `field_evidence_rerun_queue*` entries before returning diagnostics, matching nearby safe alias scrub behavior.
- Updated ROS runtime contracts with the new alias, allowed fields, fail-closed states, and forbidden raw/control material.

### Verification

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Result: PASS.
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - Result: PASS, `Ran 233 tests in 0.717s`, `OK`.

### Remaining Risk

- This is `software_proof_docker_field_evidence_rerun_queue_gate` only. It does not prove a real field rerun, real Nav2/fixed-route runtime, real task record, real elevator operation, real dropoff/cancel completion, real phone/browser validation, hardware transport, or delivery success.
- Autonomy queue producer and mobile read-only panel are owned by other workers; this Robot change is a compatible fail-closed consumer and does not wait on their implementation.

## Product Closeout Update

- Updated at: 2026-05-20 17:21 CST
- Scope: integration acceptance, sprint closeout docs, conservative OKR snapshot, and progress log only.

### Integrated Worker Changes

- Autonomy worker changed `pc-tools/evidence/field_evidence_rerun_queue.py`, `tests/test_field_evidence_rerun_queue.py`, `pc-tools/README.md`, and `docs/interfaces/evidence_contracts.md`.
- Robot worker changed `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`, `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`, and `docs/interfaces/ros_runtime_contracts.md`.
- Full-stack worker changed `mobile/web/app.js`, `mobile/web/fixtures/status.json`, `mobile/web/test_mobile_web_entrypoint.py`, and `docs/product/mobile_user_flow.md`.
- Product closeout changed `sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-done.md`, `sprints/2026.05.20_17-18_field-evidence-rerun-queue/side2side_check.md`, `sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.

### Product Acceptance

- User value: the controlled field rerun is now queueable as metadata across PC, Robot diagnostics, and mobile/web, without enabling control or claiming a real field pass.
- Product north star: phone-first delivery claims remain evidence-backed and fail-closed.
- OKR mapping: O2/O3/O4 receive software-proof support; O1 and O5 remain unchanged because their real evidence is still missing.
- Core grab: `field_evidence_rerun_queue` converts handoff intake into a queue candidate that lists real materials required before review.
- Responsible Engineers: Autonomy Algorithm Engineer, Robot Platform Engineer, and User Touchpoint Full-Stack Engineer.

### Product Validation Evidence

- Product closeout reran py_compile for Autonomy and Robot touched Python files: PASS.
- Product closeout reran `python3 -m unittest tests.test_field_evidence_rerun_queue`: PASS, `Ran 5 tests`, `OK`.
- Product closeout reran Robot diagnostics unittest: PASS, `Ran 233 tests`, `OK`.
- Product closeout reran `node --check mobile/web/app.js`: PASS.
- Product closeout reran `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`: PASS, `Ran 173 tests`, `OK`.
- Product closeout reran fixture JSON validation, CLI help, required sprint file checks, required `rg`, and scoped `git diff --check`: PASS.

### Remaining Risk

- `software_proof_docker_field_evidence_rerun_queue_gate` is not real field rerun proof.
- PR #5 merged 2026-05-14, but `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and `3269642220` is not hardware proof.
- PR #6 merged 2026-05-20 as README docs-only and did not include runtime, hardware, HIL, true phone/browser, or external cloud tests.
- `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `software_proof`, and `not_proven` remain required until real evidence arrives.
