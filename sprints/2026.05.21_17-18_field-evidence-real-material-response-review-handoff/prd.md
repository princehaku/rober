# Field Evidence Real Material Response Review Handoff PRD

Run time: 2026-05-21 17:18 CST

## User Value And Product North Star

Field owners need a clear handoff after review decision: what evidence is acceptable for later review, what is missing, what is rejected as unsafe, and what remains blocked because the real environment is unavailable. Without this handoff, the team can keep generating software-proof artifacts while field owners still do not know which concrete materials to collect next.

The product north star remains verified autonomous trash delivery for ordinary phone users. This PRD narrows the next step to evidence handoff only. It does not claim real route/elevator field pass, true phone/browser proof, O5 external cloud proof, HIL, WAVE ROVER/UART proof, delivery result, or delivery success.

## Problem

The previous `field_evidence_real_material_response_review_decision` sprint can classify response material into review decisions. The missing product step is an owner-facing handoff that turns the decision into:

- responsible owner
- next required evidence
- same safe `evidence_ref` expectation
- due/status or blocked reason
- field rerun/backfill guidance
- phone-safe copy

This handoff must preserve strict evidence boundaries because the current host has Docker-local proof only.

## OKR Mapping

| Objective | Mapping |
| --- | --- |
| Objective 2 | Clarifies the remaining route/elevator/delivery evidence required before claiming delivery or field pass. |
| Objective 3 | Requires real route/task artifacts before fixed-route or Nav2 progress can be counted as field proof. |
| Objective 4 | Gives phone/operator users a read-only support surface that explains the handoff while keeping primary actions disabled. |
| Objective 5 | Not targeted. Current O5 remains about 68% until real external cloud, 4G, OSS/CDN, DB/queue, worker/cutover, or true phone/browser evidence appears. |
| Objective 1 | Not targeted. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved; comment `3269642220` is not reviewer resolution. |

## KR Breakdown Or Update

- KR1: PC evidence gate emits `trashbot.field_evidence_real_material_response_review_handoff.v1` and safe summary schema.
- KR2: Robot diagnostics exposes only sanitized summary metadata and keeps `safe_to_control=false`.
- KR3: mobile/web shows the handoff as read-only, Chinese-first operator guidance without enabling Start Delivery, Confirm Dropoff, or Cancel.
- KR4: docs record that this is `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`, not real-world proof.
- KR5: Product closeout keeps OKR percentages conservative unless real materials arrive during implementation.

## Product Requirements

The capability name must be `field_evidence_real_material_response_review_handoff`.

The evidence boundary must be `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`.

Every artifact and summary must preserve:

- `source=software_proof`
- `status=not_proven` or equivalent `not_proven` field
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`

The handoff must include:

- prior review decision reference
- safe `evidence_ref`
- owner handoff
- next required evidence
- missing material categories
- blocked or rejected reason when applicable
- rerun/backfill guidance
- safe phone copy

The handoff must treat the following as required real evidence before any field pass claim:

- `task_record`
- `nav2_fixed_route_runtime_log`
- `route_completion_signal`
- `elevator_door_floor_evidence`
- `human_assistance_note`
- `dropoff_cancel_completion`
- `delivery_result`
- true phone/browser evidence
- diagnostics/mobile safe summary

## Non Requirements

This PRD explicitly excludes:

- real route/elevator field pass
- real dropoff/cancel completion
- delivery result or `delivery_success=true`
- true phone/browser evidence
- O5 public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or production app/device proof
- HIL or WAVE ROVER/UART proof
- PR #5 reviewer resolution or closure of `PRRT_kwDOSWB9286CJ3tX`
- new robot control paths, ACK/cursor mutation, or mobile primary-action enablement

## Priority And Acceptance Criteria

P0 acceptance:

- Autonomy gate produces a handoff artifact and summary using the required capability and boundary names.
- Robot diagnostics consumes the summary as read-only metadata and does not leak raw evidence, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER, checksums, tracebacks, or complete logs.
- mobile/web renders read-only Chinese-first handoff guidance and keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
- docs in each owner surface reflect the current capability boundary.
- Product closeout records no O5/O1 percentage movement unless real materials appear.

## Responsible Engineers

- Autonomy Algorithm Engineer owns PC gate behavior and evidence contract docs.
- Robot Platform Engineer owns Robot diagnostics safe summary and ROS runtime contract docs.
- User Touchpoint Full-Stack Engineer owns mobile/web read-only handoff and mobile user flow docs.
- Hardware Infra Engineer owns read-only source-boundary consultation against `docs/vendor/VENDOR_INDEX.md` and local vendor files.
- Product Manager / OKR Owner owns sprint closeout and conservative OKR/progress wording after worker validation.

## Risks, Blockers, And Evidence Chain

The central risk is language drift: `handoff`, `accepted`, or `ready` copy can be mistaken for real field acceptance. The implementation must use `not_proven` language and must keep the next action framed as evidence collection or owner backfill.

The evidence chain remains incomplete until a field owner supplies real materials under the same safe `evidence_ref`. The next owner-facing handoff should explicitly ask for those materials rather than creating another generic wrapper.

## Sprint Documents

This PRD belongs to:

- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/pre_start.md`
- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/prd.md`
- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/tech-plan.md`

After implementation, closeout must update `tech-done.md`, `side2side_check.md`, and `final.md`.
