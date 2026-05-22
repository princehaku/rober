# Reviewer ACK Followup Owner Response Intake Bridge PRD

Run time: 2026-05-22 21:22 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge`

## Product Problem

The previous sprint made reviewer ACK follow-up escalation status visible and safe. It can say `accepted_for_owner_response_intake_not_proven`, but the existing owner response intake mainline still accepts the older `field_evidence_material_resolution_followup_escalation_status` source path.

That leaves a product gap: support can see that reviewer ACK follow-up is ready for owner response intake, but the owner response intake gate cannot yet consume that newer safe summary as the next source of truth.

## User Value

- Field owner: sees the same safe evidence reference continue into owner response intake rather than being asked to restart from an older escalation artifact.
- Support: can route owner response material from reviewer ACK follow-up without exposing raw materials, credentials, control details, or success claims.
- Phone user: sees that the robot remains blocked and disabled until the real owner response and downstream review evidence arrive.
- Reviewer: PR #5 unresolved material state remains honest; `PRRT_kwDOSWB9286CJ3tX` is not treated as resolved by software-only metadata.

## Product North Star

The robot should be understandable and safe for ordinary users: every handoff state must explain what is missing, who owns the next evidence, and why the robot cannot be controlled yet. No local Docker metadata can become delivery success, true phone/browser proof, hardware/HIL proof, or external cloud proof.

## OKR Mapping

- Objective 5 remains the lowest objective at about 68%. This sprint supports Objective 5 evidence governance but is not O5 external proof and must not raise the OKR percentage.
- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint is not HIL or real sensor material proof.
- Objective 2/3/4 remain about 99%. This sprint is not route/elevator runtime, true phone/browser validation, field pass, verified terminal result, or delivery success.

## KR Breakdown

- KR-A: PC owner response intake safely accepts `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`, the Robot alias, and compatible wrapper shapes as source material, while preserving old source compatibility.
- KR-B: Robot diagnostics exposes the bridged owner response intake summary without raw paths, credentials, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, checksums, tracebacks, or success/control claims.
- KR-C: `mobile/web` shows the owner response intake panel with a reviewer ACK follow-up bridge fixture and keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
- KR-D: Product closeout records A/B/C evidence, keeps `software_proof` boundaries explicit, updates `OKR.md` and `docs/process/okr_progress_log.md`, and preserves no OKR percentage lift.

## Core Requirements

1. Bridge source schemas:
   - `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
   - `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
   - wrapper/nested `field_evidence_material_resolution_reviewer_ack_followup_escalation_status` summary shapes already used by Robot/mobile surfaces.
2. Preserve source compatibility with the older `field_evidence_material_resolution_followup_escalation_status` path.
3. Keep the same safe `evidence_ref`; mismatches fail closed.
4. Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
5. Reject raw artifacts, raw material contents, local filesystem paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, success claims, true phone/browser claims, Objective 5 external-proof claims, HIL claims, route/elevator field pass claims, PR #5 resolution claims, and any `delivery_success=true`.
6. Do not add action entrypoints, ACK/cursor fetch, material upload/download, owner-response route buttons, replay/resubmit, diagnostics fetch from the mobile panel, or robot command endpoints.

## Priority And Acceptance

Priority order:

1. PC bridge correctness and fail-closed source validation.
2. Robot phone-safe summary preservation.
3. Mobile read-only visibility with disabled primary actions.
4. Product closeout after implementation evidence.

Acceptance:

- Focused tests prove accepted bridge input, missing bridge input, mismatched evidence reference, unsafe claims, and disabled action states.
- Required `rg` evidence includes `software_proof`, `not true phone/browser`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- No broad test expansion; tests are fenced to the touched PC, Robot, and mobile surfaces.
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` in Product closeout unless live GitHub evidence changes.

## Responsibility

- Autonomy Algorithm Engineer owns PC gate bridge and evidence contract docs.
- Robot Platform Engineer owns diagnostics safe summary bridge and diagnostics docs.
- User Touchpoint Full-Stack Engineer owns mobile/web fixture and panel coverage.
- Product Manager / OKR Owner owns sprint closeout, OKR wording, and progress log after implementation.

## Risks And Blockers

- Docker-only host cannot prove Objective 5 external materials or true phone/browser evidence.
- The implementation must avoid turning `accepted_for_owner_response_intake_not_proven` into an owner response acceptance; it only means the source is eligible for owner response intake.
- Existing owner response intake tests may assume only the old follow-up escalation source; engineers must update focused tests without broad regression churn.
- Any real hardware or vendor detail work would require `docs/vendor/VENDOR_INDEX.md`, but this sprint should not touch hardware configuration or make new hardware claims.

