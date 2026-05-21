# Field Evidence Real Material Response Review Handoff Pre Start

Run time: 2026-05-21 17:18 CST

## Sprint Type

- sprint_type: epic
- sprint folder: `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/`
- capability: `field_evidence_real_material_response_review_handoff`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`
- planning owner: Product Manager / OKR Owner
- execution owners: Autonomy Algorithm Engineer, Robot Platform Engineer, User Touchpoint Full-Stack Engineer, Hardware Infra Engineer consultation, Product closeout

## Live Evidence Snapshot

`OKR.md` 4.1 shows Objective 5 as the current lowest objective at about 68%, but this host still has only Docker-local proof. It has no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, worker/cutover proof, production app/device proof, or true phone/browser evidence. Repeating another O5 local wrapper would not move the product toward external cloud proof.

Objective 1 is next at about 81%, but PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / material pending. GitHub comment `3269642220` is only a conservative software-proof reply publication, not reviewer resolution and not real 2D LiDAR / ToF, WAVE ROVER/UART, HIL, receipt, install, wiring, power, calibration, or operator report evidence.

The immediately actionable chain is O2/O3/O4 field material evidence. The previous sprint `field_evidence_real_material_response_review_decision` produced review decisions over field-owner material responses. This sprint continues that chain by turning the decision into field-owner handoff, next required evidence, due/status routing, and safe mobile/diagnostics copy.

## User Value And Product North Star

The user value is operational clarity for field owners: after a material response is reviewed, the next owner can see what evidence is still required, which claim remains blocked, what can be reviewed later, and what must be rerun or backfilled before anyone talks about route/elevator field pass or delivery success.

The product north star remains verified autonomous trash delivery for ordinary phone users. This sprint does not create real delivery capability; it keeps the evidence workflow honest so future real field runs can be collected under one safe `evidence_ref` without confusing software-proof metadata with real robot success.

## OKR Mapping

- Objective 2: supports the delivery/elevator chain by handing off required field evidence for route/elevator states, human assistance, dropoff/cancel completion, and delivery result.
- Objective 3: supports route/fixed-route verification by requiring real `task_record`, `nav2_fixed_route_runtime_log`, and `route_completion_signal` before field pass claims.
- Objective 4: supports the phone/operator surface by requiring the mobile UI to stay read-only and explain handoff status without enabling Start Delivery, Confirm Dropoff, or Cancel.
- Objective 5: explicitly not targeted for percentage movement; external cloud/4G/OSS/CDN/DB/queue/worker/phone-browser proof is missing.
- Objective 1: explicitly not targeted for percentage movement; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and real hardware materials are missing.

## KR Breakdown Or Update

- KR-O2-Handoff: convert prior review decision into owner handoff and next required evidence for route/elevator field materials.
- KR-O3-Traceability: preserve same safe `evidence_ref` requirements across task record, route runtime log, route completion signal, elevator door/floor material, human assistance note, dropoff/cancel completion, and delivery result.
- KR-O4-ReadOnlyPhone: expose only sanitized handoff metadata on the phone/operator path with `primary_actions_enabled=false`.
- KR-Boundary: preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false` across PC gate, Robot diagnostics, mobile/web, and Product closeout.

## Core Lever

The core lever is a fail-closed handoff contract: `field_evidence_real_material_response_review_handoff` consumes the previous review decision and emits owner-ready next steps without changing any robot control, phone action, cloud proof, hardware proof, HIL status, or OKR percentage.

## Scope

Do:

- Build a handoff gate and summary for field-owner evidence response review handoff.
- Keep the handoff output software-proof, redacted, and same-evidence-ref aware.
- Surface the handoff through Robot diagnostics and mobile/web as read-only metadata.
- Keep Product closeout conservative and update sprint closeout docs after worker validation.

Do not:

- Do not claim real field pass, real phone/browser proof, real O5 external proof, HIL, WAVE ROVER/UART proof, delivery result, or delivery success.
- Do not resolve PR #5 thread `PRRT_kwDOSWB9286CJ3tX` or treat comment `3269642220` as reviewer resolution.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch side effects, or robot control from this handoff.
- Do not expose raw artifacts, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, checksums, tracebacks, or complete internal logs.

## Priority And Acceptance

Priority is P0 for preserving evidence chain honesty before the next real field-owner run. Acceptance requires all owner surfaces to carry:

- `field_evidence_real_material_response_review_handoff`
- `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- owner handoff
- next required evidence
- same safe `evidence_ref` requirement

## Responsible Engineers

- Autonomy Algorithm Engineer: PC evidence gate, CLI/test coverage, evidence contract docs.
- Robot Platform Engineer: diagnostics safe summary and Robot runtime contract docs.
- User Touchpoint Full-Stack Engineer: read-only mobile/web handoff panel, fixture, and mobile product docs.
- Hardware Infra Engineer: read-only consultation on vendor/hardware boundary; no hardware config edits.
- Product Manager / OKR Owner: sprint closeout, OKR/progress wording only after engineers return; no OKR change in this planning task.

## Risks, Blockers, And Evidence Gaps

- Real field run materials are still missing: `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `dropoff_cancel_completion`, `delivery_result`, true phone/browser evidence, and diagnostics/mobile safe summary under the same safe `evidence_ref`.
- O5 remains blocked on real external materials: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, production app/device, and true phone/browser evidence.
- O1 remains blocked on PR #5 real hardware materials and reviewer resolution for `PRRT_kwDOSWB9286CJ3tX`.
- This sprint must not convert software-proof handoff metadata into field acceptance language.

## Sprint Documents To Create Or Update

Create now:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Future worker/product closeout after implementation:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
