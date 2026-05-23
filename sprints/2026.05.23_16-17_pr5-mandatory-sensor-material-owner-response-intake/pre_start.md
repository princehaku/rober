# PR #5 Mandatory Sensor Material Owner Response Intake - Pre Start

## Sprint Metadata

- sprint_type: epic
- Sprint folder: `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/`
- Start time: 2026-05-23 16:03 Asia/Shanghai
- Product owner: `product-okr-owner`
- Primary implementation owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- Product closeout owner: `product-okr-owner`
- Capability: `pr5_mandatory_sensor_material_owner_response_intake`
- Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`

## User Value And North Star

North star: keep `rober` moving toward a low-cost, phone-operable ROS2 trash delivery robot whose hardware assumptions are traceable before they become procurement, bringup, or HIL blockers.

This sprint value is narrow and concrete: turn the PR #5 mandatory sensor material follow-up escalation into an owner-response intake gate. Hardware/product owners can submit a safe packet with 2D LiDAR / ToF material status, and the repo classifies it as `accepted`, `missing`, `rejected`, `unsafe`, or `blocked` without claiming real hardware proof.

The outcome helps reviewers and field owners see whether the unresolved PR #5 thread can move forward, which materials are still missing, and what evidence must be provided next. It does not make the robot safer by itself and does not prove delivery.

## Evidence Read Before Planning

- `AGENTS.md`: Epic sprint planning must preserve the six-document chain and must not implement product code during planning.
- `OKR.md` 4.1, updated 2026-05-23 15:32 Asia/Shanghai: Objective 5 is lowest at about 68%; Objective 1 is next at about 81%.
- `OKR.md` line 207 area: Objective 5 should only move when at least one real material exists: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal delivery/dropoff/cancel result. This Docker-only host has none.
- `OKR.md` line 208 area: Objective 1 still needs real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry, or real WAVE ROVER environment packet material.
- `OKR.md` line 209 area: PR #5 live state is `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`.
- GitHub review-thread live check for PR #5 confirmed the same state: `PRRT_kwDOSWB9286CJ3tX` remains unresolved on `docs/product/production_hardware_boundary.md` and asks for vendor sources for mandatory sensor assumptions.
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/`: previous PR #5 rung completed `pr5_mandatory_sensor_material_followup_escalation_status` only as `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`.
- `sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/`: recent O4/current-panel proof was local browser software proof only and kept Objective 5 at about 68%, Objective 1 at about 81%, and `PRRT_kwDOSWB9286CJ3tX` unresolved.
- `docs/vendor/VENDOR_INDEX.md`: local vendor files prove the source boundary for Orange Pi Zero 3 and WAVE ROVER UART newline-delimited JSON references, but do not prove project 2D LiDAR / ToF SKU, purchase, installation, wiring, power, calibration, HIL, route/elevator field pass, or delivery success.
- `docs/product/production_hardware_boundary.md`: current hardware boundary already states LiDAR/ToF material is `hardware_material_pending`, `not_proven`.
- `docs/product/mobile_user_flow.md`: phone surface must stay read-only for diagnostic/support material panels and must keep Start Delivery, Confirm Dropoff, and Cancel fail closed unless existing action gates explicitly allow them.

## Why Not Objective 5 This Round

Objective 5 remains the numeric lowest objective at about 68%, but the current repo evidence says the next O5 lift requires real external material. The Docker-only host does not have public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal delivery/dropoff/cancel result material.

The last two relevant runs already consumed local-only proof paths: O5 terminal-result owner-response review-decision metadata and O4 current-panel browser proof refresh. Continuing to add local O5 metadata would repeat the same missing-external-material blocker and would not improve OKR completion.

## Objective Target

- Targeted objective: Objective 1, hardware protocol and trustworthy hardware boundary, about 81%.
- Reason: PR #5 still has the unresolved mandatory sensor assumption review thread `PRRT_kwDOSWB9286CJ3tX`; the next software-only rung is to intake owner responses to the previous escalation summary.
- Completion boundary: no OKR percentage lift unless real material appears and reviewer state changes. This sprint should keep Objective 1 around 81% and Objective 5 around 68% if only Docker/software proof is produced.

## KR Breakdown

- KR-A Hardware: create a PC gate that consumes the prior `pr5_mandatory_sensor_material_followup_escalation_status` safe summary plus a sanitized field/hardware owner response packet, then emits `accepted`, `missing`, `rejected`, `unsafe`, or `blocked`.
- KR-B Robot: expose a Robot diagnostics safe alias for the owner-response intake summary without raw packets or control grants.
- KR-C Full-Stack: expose the owner-response intake result in `mobile/web` as a read-only support panel, preserving disabled primary actions.
- KR-D Product: close the Epic only as software proof, update sprint closeout docs and conservative OKR/progress-log language after implementation, and preserve unresolved PR-thread state unless live GitHub evidence changes.

## Core Lever

The core lever is not another generic blocker display. It is the next rung after follow-up escalation: `pr5_mandatory_sensor_material_owner_response_intake`.

The gate must classify owner response materials in a way that is actionable for PR #5 reviewers while preserving:

- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Scope Boundaries

In scope for implementation after this planning phase:

- PC evidence gate and focused tests for owner-response intake.
- Hardware/vendor boundary documentation updates that cite `docs/vendor/VENDOR_INDEX.md`.
- Robot diagnostics safe alias and focused tests.
- `mobile/web` read-only panel, fixture, and focused tests.
- Product closeout docs, OKR/progress-log updates, and final evidence boundary review.

Out of scope:

- Resolving PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Claiming LiDAR/ToF installed, purchased, wired, calibrated, or HIL-proven.
- Claiming WAVE ROVER/UART/HIL proof.
- Claiming route/elevator field pass, verified terminal result, true phone/browser, Objective 5 external proof, or delivery success.
- Enabling Start Delivery, Confirm Dropoff, Cancel, or any robot-control path.
- Editing product code during this planning-only task.

## Risks And Blockers

- Real materials may still be absent; accepted intake must mean "accepted for review as safe metadata" only, not installed/proven hardware.
- Vendor/source references can prevent hardware guessing but cannot prove project 2D LiDAR / ToF procurement or HIL.
- The mobile panel can be misread as a field-ready state; it must use explicit `not_proven`, `hardware_material_pending`, and disabled-action copy.
- GitHub thread state can change externally; Product closeout must re-check PR #5 before claiming any thread status.

## Sprint Documents To Create Or Update

Created in this planning task:

- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/pre_start.md`
- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/prd.md`
- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/tech-plan.md`

Implementation and closeout must later update:

- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/tech-done.md`
- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/side2side_check.md`
- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- Relevant `docs/product/` and `docs/interfaces/` files changed by the implementation owners.
