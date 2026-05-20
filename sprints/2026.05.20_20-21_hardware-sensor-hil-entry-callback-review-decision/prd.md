# Hardware Sensor HIL-entry Callback Review Decision PRD

## User Value

The unresolved PR #5 sensor-source thread is blocked on real material evidence. Field and hardware owners need a single review decision that says which HIL-entry callback materials are accepted, missing, rejected, or unsafe before anyone asks for reviewer resolution or updates OKR progress.

## OKR Mapping

- Objective 1: improves the software-proof review chain for real 2D LiDAR / ToF and HIL-entry material callbacks.
- Objective 4: mobile/web can read the decision safely, but this is not real phone acceptance.
- Objective 5: not targeted; no external cloud proof is added.

## Product Requirements

- Add `hardware_sensor_hil_entry_callback_review_decision` artifact and summary.
- Input must be the prior `hardware_sensor_hil_entry_callback_intake` artifact/summary or Robot-safe wrapper.
- Output must include review decision, accepted/missing/rejected callback material groups, decision reasons, next required evidence, owner handoff, safe rerun command, safe evidence ref, and proof boundary.
- Missing, unsupported, mismatched, unsafe, weak-contract, success-claim, or control-claim cases must fail closed.
- Robot diagnostics and mobile/web must consume only sanitized summary fields.

## Acceptance Boundary

The accepted result is `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`. It does not prove real hardware, real procurement, real installation, real calibration, real HIL-entry pass, real Nav2/SLAM field pass, PR #5 thread resolution, or delivery success.
