# Field Evidence Real Material Request Dispatch Final

Run time: 2026-05-21 14:22 CST

## Final Verdict

Accepted as `software_proof_docker_field_evidence_real_material_request_dispatch_gate`.

This sprint successfully dispatches a field-owner real-material request for one same safe `evidence_ref`. It does not increase any OKR percentage because it does not include real materials, real robot runtime, real phone/browser, real cloud, HIL, or delivery success.

## User Value And North Star

The user value is concrete execution pressure: the next field owner no longer receives an abstract blocker, but a named checklist of the exact real materials needed to review O2/O3/O4. The product north star remains verified autonomous trash delivery with one reconciled evidence chain across route/task, elevator/human assist, terminal result, phone/browser, and diagnostics.

## What Shipped

- Autonomy added `field_evidence_real_material_request_dispatch` PC gate and focused tests.
- Robot added `robot_diagnostics_field_evidence_real_material_request_dispatch_summary` safe alias and diagnostics tests.
- Full-Stack added the mobile “现场真实材料请求” read-only panel, fixture, and tests.
- Hardware provided read-only vendor-boundary consultation from `docs/vendor/VENDOR_INDEX.md` and WAVE ROVER files.
- Docs were updated in `pc-tools/README.md`, `docs/interfaces/evidence_contracts.md`, `docs/interfaces/ros_runtime_contracts.md`, and `docs/product/mobile_user_flow.md`.
- Product closeout updated `tech-done.md`, `side2side_check.md`, this `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.

## OKR Closeout

| Objective | Closeout decision |
| --- | --- |
| Objective 1 | Remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending; comment `3269642220` is not reviewer resolution. No real WAVE ROVER/UART/HIL or sensor material arrived. |
| Objective 2 | Remains about 99%. The request names route/elevator/dropoff materials but does not prove real delivery, elevator, dropoff/cancel completion, or delivery result. |
| Objective 3 | Remains about 99%. The request names `task_record`, `nav2_fixed_route_runtime_log`, and `route_completion_signal`, but no real route runtime material arrived. |
| Objective 4 | Remains about 99%. The mobile panel is useful and safe, but it is not true phone/browser evidence or production app/device proof. |
| Objective 5 | Remains about 68%. This sprint does not provide public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, production app/device, or external phone/browser proof. |

## Evidence Boundary

The accepted boundary is:

- `software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

This is not real field rerun, not real `task_record`, not real `nav2_fixed_route_runtime_log`, not real `route_completion_signal`, not route/elevator field pass, not true phone/browser proof, not dropoff/cancel completion, not delivery result, not delivery success, not HIL, not WAVE ROVER/UART proof, not O5 external proof, and not PR #5 reviewer resolution.

## Validation Summary

Product closeout validation and targeted integration validation are required at closeout and must be reported in the chat final response:

- closeout file checks
- required evidence-boundary `rg`
- closeout scoped `git diff --check`
- targeted `py_compile`
- Autonomy unittest
- Robot diagnostics unittest
- `node --check`
- mobile fixture JSON validation
- mobile unittest
- integration required `rg`
- implementation scoped `git diff --check`

## Remaining Risks And Next Evidence

- Field owner still needs to return the nine real materials under one same safe `evidence_ref`: `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `dropoff_cancel_completion`, `delivery_result`, `true_phone_browser_evidence`, and `diagnostics_mobile_safe_summary`.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` still needs real vendor-sourced 2D LiDAR / ToF material and reviewer resolution before Objective 1 can move.
- Objective 5 still needs real external cloud / 4G / OSS/CDN / DB/queue / production worker / production phone/browser evidence before the 68% plateau can move.
