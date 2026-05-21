# Field Evidence Real Material Response Intake PRD

Run time: 2026-05-21 15:16 CST

## Product Problem

The project has already dispatched a field-owner request for nine real-material categories. The next product gap is not another request, backfill, or local O5 metadata wrapper. The gap is safe response intake: when a field owner replies with materials or blockers, the system needs a conservative way to classify each category as `accepted`, `missing`, `rejected`, or `blocked` without converting partial material into delivery success.

Objective 5 remains the lowest Objective at about 68%, but it cannot move without real public HTTPS/TLS, 4G/SIM, OSS/CDN, DB/queue, worker/cutover, production app/device, or true phone/browser evidence. Objective 1 remains blocked because PR #5 `PRRT_kwDOSWB9286CJ3tX` is unresolved and comment `3269642220` is not reviewer resolution or real hardware proof. Therefore this sprint focuses on O2/O3/O4 field-material response intake.

## User Value And Product North Star

Field owners need a response path that tells them whether returned material is acceptable for later review, missing, rejected for safety/schema/evidence mismatch, or blocked by field conditions. Operators and support need the response to remain phone-safe and fail-closed, with Start Delivery, Confirm Dropoff, and Cancel still disabled unless a later real proof explicitly changes the control boundary.

The product north star is verified autonomous trash delivery: a phone user can trust a completed task only after real route/task runtime, elevator/human-assist evidence, terminal result, true phone/browser observation, diagnostics/mobile summary, and hardware boundaries reconcile to one safe `evidence_ref`.

## OKR Mapping

| Objective | Current state | Product decision |
| --- | --- | --- |
| Objective 5 | About 68%, lowest. | Do not add local O5 metadata. Require real external proof before moving the percentage. |
| Objective 1 | About 81%. | Do not claim PR #5 closure until `PRRT_kwDOSWB9286CJ3tX` is resolved with real vendor-sourced mandatory sensor materials; comment `3269642220` remains software-proof publication only. |
| Objective 2 | About 99%, missing real delivery/elevator proof. | Intake field responses for elevator door/floor evidence, human assistance, dropoff/cancel completion, and delivery result. |
| Objective 3 | About 99%, missing real route proof. | Intake field responses for `task_record`, Nav2/fixed-route runtime log, and route completion signal. |
| Objective 4 | About 99%, missing real device/browser proof. | Intake true phone/browser evidence and diagnostics/mobile safe summary while preserving disabled primary actions. |

## KR Breakdown

KR1: Define the response-intake classification contract.

- The capability name is `field_evidence_real_material_response_intake`.
- The evidence boundary is `software_proof_docker_field_evidence_real_material_response_intake_gate`.
- Every returned category must be classified as `accepted`, `missing`, `rejected`, or `blocked`.
- `accepted` means accepted for later review only; it is not delivery success, not route/elevator pass, and not OKR completion by itself.

KR2: Preserve safety and proof boundaries.

- Required invariant fields: `source=software_proof`, `status=not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Missing previous request dispatch, missing `evidence_ref`, mixed `evidence_ref`, unsafe claims, raw credentials, raw ROS topics, `/cmd_vel`, serial/UART details, local paths, tracebacks, or complete artifacts must fail closed.
- Response intake must not enable Start Delivery, Confirm Dropoff, Cancel, ACK/cursor control, robot commands, or hardware actuation.

KR3: Split response families by owner.

- Autonomy owns route/task response classification for `task_record`, `nav2_fixed_route_runtime_log`, and `route_completion_signal`.
- Robot owns diagnostics-safe response-intake summary and fail-closed alias.
- Full-Stack owns mobile-safe read-only response state display and true phone/browser response semantics.
- Hardware owns read-only consultation for elevator, human-assistance, mandatory sensor, WAVE ROVER/UART/HIL, and vendor-source boundaries.

KR4: Keep closeout conservative.

- `OKR.md` may only be updated after execution closeout.
- No Objective percentage should move unless real materials are actually accepted and reviewed under the correct evidence boundary.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless reviewer state changes live; `3269642220` remains a software-proof reply publication.

## Core User Story

As a field owner, I need to submit real route/elevator/dropoff/phone materials or explain why they are blocked, so Product and Engineers can classify each material safely without guessing, losing the same safe `evidence_ref`, or overstating partial evidence as delivery success.

## Required Capability

Capability name: `field_evidence_real_material_response_intake`

Expected response-intake output:

- source request reference from `field_evidence_real_material_request_dispatch`
- same safe `evidence_ref`
- material category status map
- accepted material summaries, redacted and phone-safe
- missing material list
- rejected material list with reason codes
- blocked material list with owner next steps
- explicit disabled action fields
- explicit blocked claims
- next step for Product review and Engineering follow-up

Required status vocabulary:

- `accepted`
- `missing`
- `rejected`
- `blocked`

Required blocked claims:

- real field rerun
- true phone/browser proof
- Nav2/fixed-route proof
- route/elevator field pass
- HIL pass
- WAVE ROVER/UART proof
- O5 external proof
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved
- delivery result
- delivery_success

## Acceptance Criteria

Planning acceptance for this task:

- `pre_start.md`, `prd.md`, and `tech-plan.md` exist under `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/`.
- The docs include `sprint_type: epic`, `field_evidence_real_material_response_intake`, `software_proof_docker_field_evidence_real_material_response_intake_gate`, `Objective 5`, `Objective 1`, `PRRT_kwDOSWB9286CJ3tX`, `3269642220`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- `tech-plan.md` includes `## OKR 最低优先级核对`.
- The plan names four parallel owners: Autonomy, Robot, Full-Stack, and Hardware read-only consultation.

Execution acceptance for the following engineering stage:

- The response-intake gate or artifact consumes the previous request dispatch state and classifies the nine required material categories.
- The output preserves `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Unsafe, mismatched, stale, or success-claiming materials are `rejected`, not silently accepted.
- Missing field-owner materials are `missing`; unavailable real-world dependencies are `blocked`.
- Related `docs/` pages are updated during execution to reflect the new response-intake contract.
- Fenced validation only: focused Python/unit checks, `node --check`, fixture validation, required `rg`, and scoped `git diff --check`.

## Priority And Responsible Engineers

Priority P0:

- Autonomy Algorithm Engineer: route/task material response schema and classifier expectations.
- Robot Platform Engineer: response-intake artifact, diagnostics-safe summary, fail-closed metadata boundary.
- User Touchpoint Full-Stack Engineer: read-only mobile response status surface and phone/browser response language.

Priority P1:

- Hardware Infra Engineer: read-only consultation for vendor-source and hardware-adjacent boundaries. Hardware must not change WAVE ROVER, UART, LiDAR, ToF, power, pins, firmware, or mechanical assumptions in this sprint unless a later execution task explicitly expands scope and cites `docs/vendor/VENDOR_INDEX.md`.

Product Manager / OKR Owner owns user value, OKR mapping, sprint evidence chain, and closeout language.

## Risks And Evidence Gaps

- If no field-owner replies exist yet, execution can only produce `missing` or `blocked` response intake, not accepted materials.
- If returned materials use different `evidence_ref` values, the response must be rejected or blocked until reconciled.
- If mobile/browser screenshots or logs are synthetic, local-only, or missing device evidence, they cannot count as true phone/browser proof.
- If any material implies route/elevator pass, HIL, delivery result, delivery_success, O5 external proof, or PR #5 reviewer resolution without real evidence, Product closeout must reject that claim.
