# Field Evidence Real Material Request Dispatch PRD

Run time: 2026-05-21 14:15 CST

## Product Problem

The project has enough local software-proof wrappers around field evidence rerun, callback intake, review, acceptance packet, and acceptance backfill. The missing product input is no longer another local wrapper; it is a field-owner request that names the exact real materials needed to move O2/O3/O4 evidence from `not_proven` toward future acceptance.

Objective 5 is still the lowest objective at about 68%, but real O5 materials are unavailable. Objective 1 is next lowest at about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and comment `3269642220` does not resolve the reviewer request for vendor-sourced mandatory sensor assumptions. Therefore the next useful product move is to request real O2/O3/O4 materials tied to the same safe `evidence_ref`.

## User Value And North Star

Field owners need a checklist they can execute during a real route/elevator/phone trial without guessing which files, screenshots, logs, or notes count. Operators and support need the resulting request to be phone-safe and fail-closed so missing material never appears as delivery success.

The north star is still verified autonomous trash delivery: task start, route movement, elevator or human-assisted transition, dropoff or cancel, phone/browser observation, and delivery result all reconcile to one safe evidence chain before the product claims completion.

## OKR Mapping

| Objective | Current state | Product decision |
| --- | --- | --- |
| Objective 5 | About 68%, lowest. | Do not add another local O5 wrapper without real public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, production app/device, or true phone/browser proof. |
| Objective 1 | About 81%. | Do not claim PR #5 closure until `PRRT_kwDOSWB9286CJ3tX` is resolved with vendor-sourced mandatory sensor assumptions; comment `3269642220` remains software-proof publication only. |
| Objective 2 | About 99%, but missing delivery field proof. | Request real dropoff/cancel completion, delivery result, elevator door/floor state, and human assistance notes. |
| Objective 3 | About 99%, but missing route runtime proof. | Request real `task_record`, Nav2/fixed-route runtime log, and route completion signal for the same safe `evidence_ref`. |
| Objective 4 | About 99%, but missing real device proof. | Request true phone/browser evidence and diagnostics/mobile safe summary from the same field run. |

## KR Breakdown

KR1: Define a request artifact contract for `field_evidence_real_material_request_dispatch`.

- It must read or cite the previous acceptance backfill safe evidence state.
- It must preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- It must output a field-owner checklist that is executable without exposing raw ROS topics, credentials, serial paths, checksums, or complete artifacts.

KR2: Split the required real materials by evidence family.

- Route/task: `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`.
- Elevator/field assist: `elevator_door_floor_evidence`, `human_assistance_note`.
- Terminal task result: `dropoff_cancel_completion`, `delivery_result`.
- User touchpoint: `true_phone_browser_evidence`, `diagnostics_mobile_safe_summary`.

KR3: Keep claim boundaries machine-checkable.

- The artifact must state `software_proof_docker_field_evidence_real_material_request_dispatch_gate`.
- It must state that the request is not real field rerun, not true phone/browser proof, not Nav2/fixed-route proof, not route/elevator field pass, not O5 external proof, not HIL, not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, not delivery result, and not delivery success.

## Core User Story

As a field owner, I need one request package that tells me exactly which same-`evidence_ref` real materials to capture during a route/elevator/dropoff/phone trial, so I can hand back evidence that Product, Robot, Autonomy, Full-Stack, and Hardware can review without confusing software-proof readiness with real field acceptance.

## Required Capability

Capability name: `field_evidence_real_material_request_dispatch`

Evidence boundary: `software_proof_docker_field_evidence_real_material_request_dispatch_gate`

The capability should produce or document a request package that contains:

- source acceptance state from the prior backfill summary
- same safe `evidence_ref` requirement
- required materials list
- owner mapping for each material
- accepted format hints
- redaction and phone-safety constraints
- explicit `not_proven` boundary and disabled primary action fields
- next-step states for field owner, Product review, and engineering intake

## Acceptance Criteria

Planning acceptance for this task:

- `pre_start.md`, `prd.md`, and `tech-plan.md` exist under the new sprint folder.
- The docs include `sprint_type: epic`, `field_evidence_real_material_request_dispatch`, `software_proof_docker_field_evidence_real_material_request_dispatch_gate`, `Objective 5`, `Objective 1`, `PRRT_kwDOSWB9286CJ3tX`, `3269642220`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- `tech-plan.md` includes `## OKR 最低优先级核对`.

Execution acceptance for the following engineering stage:

- The implementation must create a request artifact or gate that asks for the nine required material categories.
- The request must fail closed when prior acceptance state is missing, unsafe, stale, or from a mismatched `evidence_ref`.
- The request must not enable Start Delivery, Confirm Dropoff, Cancel, or any primary action.
- The docs in `docs/` must be updated during execution to reflect the new request contract.
- `OKR.md` may be updated only at closeout and only with conservative language unless real materials arrive.

## Priority And Responsible Engineers

Priority P0:

- Autonomy Algorithm Engineer owns route/task material requirements and Nav2/fixed-route runtime expectations.
- Robot Platform Engineer owns diagnostics-safe artifact generation and fail-closed metadata boundary.
- User Touchpoint Full-Stack Engineer owns true phone/browser evidence checklist and mobile-safe display semantics.

Priority P1:

- Hardware Infra Engineer owns elevator door/floor evidence, human-assistance note, and hardware-adjacent boundary review. This does not include changing WAVE ROVER, UART, LiDAR, ToF, or mechanical configuration in this sprint unless a later execution plan explicitly expands scope and cites vendor files.

Product Manager / OKR Owner owns KR mapping, acceptance boundary, sprint evidence chain, and OKR closeout language.

## Risks And Evidence Gaps

- Real O5 evidence remains absent, so Objective 5 should stay about 68% until external cloud/4G/OSS/CDN/DB/queue/phone materials arrive.
- Real O1 evidence remains absent, so Objective 1 should stay about 81% until PR #5 `PRRT_kwDOSWB9286CJ3tX` is resolved with vendor-sourced mandatory sensor assumptions and real hardware/HIL materials.
- O2/O3/O4 progress still cannot move from this planning sprint alone; it needs the field owner to return same-`evidence_ref` real materials.
- The request must not become a new wrapper that claims readiness without material intake.
