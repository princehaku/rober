# Field Evidence Real Material Response Intake Pre-Start

Run time: 2026-05-21 15:16 CST

## Sprint Declaration

- sprint_type: epic
- capability: `field_evidence_real_material_response_intake`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_intake_gate`
- planning owner: Product Manager / OKR Owner
- execution owner split:
  - Autonomy Algorithm Engineer: route/task and Nav2/fixed-route response classification.
  - Robot Platform Engineer: diagnostics-safe response-intake artifact and fail-closed summary.
  - User Touchpoint Full-Stack Engineer: field-owner/mobile-safe response status surface.
  - Hardware Infra Engineer: read-only consultation for vendor-source, elevator, human-assistance, LiDAR/ToF, WAVE ROVER/UART/HIL boundary checks.

## Background Evidence

- `OKR.md` 4.1 currently shows Objective 5 at about 68%, the lowest numeric Objective. It remains blocked because no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, or true phone/browser evidence has arrived. Per stop rule, this sprint must not add another local O5 metadata wrapper.
- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending. GitHub reply comment `3269642220` is only software-proof publication, not reviewer resolution, and it does not provide real 2D LiDAR / ToF / WAVE ROVER / UART / HIL materials.
- The latest sprint `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/final.md` accepted `software_proof_docker_field_evidence_real_material_request_dispatch_gate` and dispatched nine real-material requests for O2/O3/O4 under one same safe `evidence_ref`. It explicitly did not prove delivery, route/elevator field pass, real phone/browser, HIL, or O5 external proof.
- The next useful step is response intake: field-owner replies must be classified as `accepted`, `missing`, `rejected`, or `blocked`, while preserving `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## User Value And Product North Star

The user value is turning field-owner replies into reviewable product evidence without accidentally treating partial or unsafe material as success. A field owner should be able to return files, screenshots, notes, or blockers and receive a clear status: accepted for later review, missing required material, rejected for unsafe or mismatched content, or blocked by environment/material availability.

The product north star remains verified autonomous trash delivery: one same safe evidence chain must reconcile route/task runtime, elevator/human assist, terminal dropoff/cancel result, true phone/browser observation, diagnostics/mobile summary, and hardware boundaries before the project claims route/elevator field pass or delivery success.

## OKR Mapping

- Objective 5: numerically lowest at about 68%, but not targeted for local progress because real external materials are absent. This sprint records the stop-rule pivot rather than repeating O5 metadata.
- Objective 1: next lowest at about 81%, but not targeted for progress because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and comment `3269642220` does not provide real mandatory sensor or HIL materials.
- Objectives 2/3/4: near complete but waiting on real field materials. This sprint targets their evidence chain by creating the response-intake plan for the nine dispatched material categories.

## Core Lever

Consume field-owner responses to the previous request dispatch and classify each required material category:

- `task_record`
- `nav2_fixed_route_runtime_log`
- `route_completion_signal`
- `elevator_door_floor_evidence`
- `human_assistance_note`
- `dropoff_cancel_completion`
- `delivery_result`
- `true_phone_browser_evidence`
- `diagnostics_mobile_safe_summary`

Each category must keep a safe `evidence_ref` and one of four statuses:

- `accepted`: material is present, safe, same-evidence-ref, and ready for later review; still not a final pass.
- `missing`: required material was not returned.
- `rejected`: material is present but unsafe, stale, mismatched, success-claiming, or outside phone-safe/vendor-safe boundaries.
- `blocked`: field owner reports an external/hardware/field condition that prevents material capture.

## Scope Boundary

In scope for this planning task:

- Create `pre_start.md`, `prd.md`, and `tech-plan.md` for the new Epic sprint.
- Define product value, OKR mapping, KR split, owner split, file scope, and fenced validation commands.
- Preserve `software_proof_docker_field_evidence_real_material_response_intake_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

Out of scope for this planning task:

- No product code, tests, mobile UI, Robot diagnostics code, PC gates, hardware configuration, `OKR.md`, or `docs/` changes.
- No claim of real field rerun, real Nav2/fixed-route proof, real elevator proof, true phone/browser proof, delivery result, delivery_success, HIL, WAVE ROVER/UART proof, O5 external proof, or PR #5 reviewer resolution.
- No hardware detail changes. If later execution touches WAVE ROVER, UART, LiDAR, ToF, pins, voltage, baudrate, JSON commands, feedback protocol, or mechanical dimensions, Hardware must re-read `docs/vendor/VENDOR_INDEX.md` and cited local vendor files.

## Blocker Reuse Check

The previous sprint consumed the real-material absence once by dispatching requests. This sprint does not repeat the same dispatch wrapper; it advances the ladder into response intake and classifies actual replies or explicit missing/blocked states. If no field-owner reply exists during execution, the output must classify the response as `blocked` or `missing`, not invent material or claim acceptance.

## Required Sprint Documents

Created in this planning task:

- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/pre_start.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/prd.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/tech-plan.md`

Required after execution:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
