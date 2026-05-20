# Hardware Sensor HIL-entry Callback Review Decision Side-by-side Check

## Acceptance Check

| Requirement | Result | Evidence |
| --- | --- | --- |
| Fresh sprint folder and epic plan | Passed | `pre_start.md`, `prd.md`, `tech-plan.md`, and `tech-done.md` exist for `2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision`. |
| OKR lowest-priority rerank recorded | Passed | `tech-plan.md` states O5 is lowest but blocked on missing real external materials, so this sprint targets O1 / PR #5 unresolved hardware material evidence chain. |
| PC gate created | Passed | `hardware_sensor_hil_entry_callback_review_decision_gate.py` emits artifact and summary under `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`. |
| Robot safe alias created | Passed | `robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary` exposes sanitized metadata only. |
| Mobile read-only panel created | Passed | mobile/web adds “传感器 HIL 回调复核决策” and keeps main actions disabled. |
| Verification fenced | Passed | PC gate 7 tests OK, Robot diagnostics 237 tests OK, mobile 179 tests OK, JSON checks, `node --check`, required `rg`, and scoped `git diff --check` passed. |
| Evidence boundary preserved | Passed | `software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false` remain explicit. |

## Non-claims

This sprint is not real hardware proof, not HIL, not PR #5 reviewer resolution, not O5 external proof, not real phone/browser proof, not route/elevator field pass, and not delivery success.
