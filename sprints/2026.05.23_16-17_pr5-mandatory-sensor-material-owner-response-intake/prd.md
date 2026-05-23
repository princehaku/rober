# PR #5 Mandatory Sensor Material Owner Response Intake - PRD

## Product North Star

`rober` should be a low-cost ROS2 trash delivery robot that ordinary users can operate from a phone, while hardware assumptions remain traceable enough for procurement, bringup, HIL, and reviewer decisions. This sprint supports that north star by preventing mandatory sensor assumptions from becoming hidden hardware debt.

## User Value

The user value is support and delivery reliability, not a new control feature. When PR #5 asks for mandatory sensor evidence, a field or hardware owner needs a safe way to respond with material status and have the repo classify it consistently.

This sprint gives owners and reviewers a shared intake result:

- `accepted`: safe owner response received, still not proof.
- `missing`: required material references are absent.
- `rejected`: response contradicts required source/material contract.
- `unsafe`: response contains unsafe copy, raw material, credentials, control claims, HIL/pass claims, or delivery-success claims.
- `blocked`: previous escalation summary or owner response cannot be consumed safely.

The ordinary phone user should not see raw hardware artifacts or confusing control states. The phone-facing result must remain read-only and explain that primary actions remain disabled.

## Problem

PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved because `docs/product/production_hardware_boundary.md` introduced mandatory sensor assumptions that need vendor-source or real-material evidence. Previous work completed source alignment and follow-up escalation status, but it did not consume an actual owner response packet.

Without an owner-response intake gate, the team has no fenced way to distinguish:

- an acceptable safe response that is ready for review;
- a response that is still missing LiDAR/ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry materials;
- an unsafe or over-claiming response that must not enter Robot/mobile diagnostics.

## OKR Mapping

- Objective 5: remains lowest at about 68%, but this sprint does not target it. `OKR.md` requires real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal delivery/dropoff/cancel result material before more O5 completion work. This host is Docker-only and has none of those materials.
- Objective 1: target objective at about 81%. The unresolved PR #5 sensor-material thread blocks the hardware boundary from becoming trustworthy. This sprint advances the software-proof evidence chain but should not lift Objective 1 unless real material or reviewer resolution appears.
- Objective 4: touched only through a read-only mobile support panel. No true phone/browser proof and no primary action enablement.
- Objectives 2 and 3: not targeted. No route/elevator field pass, Nav2/fixed-route runtime, task record, or delivery result is produced.

## KR Breakdown

### KR-A: Hardware Owner Response Intake

Hardware creates the PC gate for `pr5_mandatory_sensor_material_owner_response_intake`. The gate consumes:

- prior `pr5_mandatory_sensor_material_followup_escalation_status` safe summary;
- a sanitized field/hardware owner response packet;
- `docs/vendor/VENDOR_INDEX.md` as the local source-boundary reference.

The output must classify the owner response as `accepted`, `missing`, `rejected`, `unsafe`, or `blocked`, and must keep `software_proof`, `hardware_material_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

### KR-B: Robot Diagnostics Safe Alias

Robot exposes only a safe summary alias, expected as `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary`. The alias must not expose raw owner response packets, artifact paths, credentials, serial/UART details, ROS topics, `/cmd_vel`, or any control grant.

### KR-C: Mobile Read-Only Support Panel

Full-Stack adds a `mobile/web` read-only panel for the owner-response intake result. It must:

- consume Robot safe summary first;
- show the decision, safe `evidence_ref`, missing/rejected/unsafe reasons, next required evidence, and proof boundary;
- keep Start Delivery, Confirm Dropoff, and Cancel disabled through existing gates;
- preserve `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

### KR-D: Product Closeout And OKR Boundary

Product closes the sprint only as `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`, updates OKR/progress-log language conservatively, and re-checks live PR #5 thread state before final wording.

## Scope

In scope:

- Owner-response intake classification.
- Safe summaries for PC, Robot diagnostics, and mobile support view.
- Focused tests and JSON validation.
- Documentation updates under relevant `docs/` paths.
- Sprint closeout and OKR/progress-log updates after implementation.

Out of scope:

- Publishing a GitHub reply or resolving `PRRT_kwDOSWB9286CJ3tX`.
- Proving 2D LiDAR / ToF SKU/source/receipt/procurement, installation, wiring, power, calibration, or HIL.
- Proving WAVE ROVER/UART, `/odom`, `/imu/data`, `/battery`, or real HIL.
- Proving true phone/browser, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, route/elevator field pass, verified terminal result, or delivery success.
- Enabling primary user actions.

## Evidence Chain

The implementation must preserve this chain:

1. `docs/vendor/VENDOR_INDEX.md` establishes local vendor-source coverage for Orange Pi Zero 3 and WAVE ROVER UART newline-delimited JSON references.
2. That vendor coverage does not prove 2D LiDAR / ToF SKU, procurement, installation, wiring, power, calibration, or HIL.
3. `pr5_mandatory_sensor_material_followup_escalation_status` records that the PR #5 material follow-up remains safe and pending.
4. `pr5_mandatory_sensor_material_owner_response_intake` consumes a safe owner response and classifies it without upgrading proof state.
5. Future review-decision or review-handoff rungs may proceed only from the safe intake output.

## Acceptance Criteria

- The implementation outputs `pr5_mandatory_sensor_material_owner_response_intake`.
- The implementation outputs `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`.
- Summaries include `hardware_material_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Owner response classification is limited to `accepted`, `missing`, `rejected`, `unsafe`, or `blocked`.
- `docs/vendor/VENDOR_INDEX.md` is cited as the hardware source-boundary entrypoint.
- PR #5 thread state remains explicit: `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`, unless live GitHub state changes.
- Mobile/web panel is read-only and does not create new robot commands or enable primary actions.
- Product closeout states no OKR percentage lift unless real external/hardware/reviewer evidence appears.

## Priority And Owners

P0 Hardware:

- PC gate and hardware/vendor docs.
- Source-boundary enforcement using `docs/vendor/VENDOR_INDEX.md`.

P0 Robot:

- Diagnostics safe alias and interface docs.
- Focused diagnostics tests.

P0 Full-Stack:

- Mobile/web read-only support panel, fixture, and focused UI tests.
- Product-flow docs for phone-safe behavior.

P1 Product:

- Sprint closeout docs, OKR/progress-log conservative update, and live PR-state check.

## Risks And Required Evidence To Fill Later

- Real 2D LiDAR / ToF materials are still missing until SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry materials are provided.
- Real WAVE ROVER/UART/HIL materials are still missing until powered bench or robot logs exist with a safe `evidence_ref`.
- Real Objective 5 progress is still blocked on public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal result material.
- Real delivery remains unproven until route/elevator field pass, Nav2/fixed-route runtime, task record, dropoff/cancel completion, and delivery result materials exist.
