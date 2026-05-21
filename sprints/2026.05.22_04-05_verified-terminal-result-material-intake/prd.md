# Verified Terminal Result Material Intake PRD

Run time: 2026-05-22 04:05 Asia/Shanghai

## Product Summary

`verified_terminal_result_material_intake` is a fail-closed material intake capability for terminal delivery/dropoff/cancel result evidence. It lets a field owner provide one JSON evidence bundle, validates whether the bundle is safe and complete enough for review, and produces a sanitized summary that Robot diagnostics and mobile/web can display without enabling robot control.

This is not a success detector. It is a verification gate for incoming field material. The required output boundary is `software_proof_docker_verified_terminal_result_material_intake_gate`, with `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` unless future real material is supplied and accepted through a separate closeout decision.

## User Value And Product North Star

User value: support and field owners need a single, conservative place to submit and inspect terminal result materials instead of relying on chat, scattered panels, or truthy fields that might falsely imply delivery success.

Product north star: a normal user should only see task completion when a real terminal delivery/dropoff/cancel result is verified under the same safe `evidence_ref`; before that, the phone experience must explain what is pending and keep motion-related actions disabled.

## OKR Mapping

- Objective 5 remains the lowest current Objective at about 68%. This sprint targets the part of Objective 5 that depends on verified terminal delivery/dropoff/cancel result material rather than another local O5 metadata layer.
- Objective 2 and Objective 3 benefit only as downstream consumers when real route/elevator/task materials are later provided. This sprint does not prove real route/elevator field pass, Nav2/fixed-route runtime, dropoff completion, cancel completion, or delivery result.
- Objective 4 benefits through a read-only phone-safe panel. This sprint does not prove real iPhone/Android behavior, production app, PWA prompt/user choice, or true browser/device acceptance.
- Objective 1 remains blocked on real hardware materials. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` stays unresolved / material pending unless reviewer state changes and real materials are provided.

## KR Breakdown

1. KR-A Autonomy intake: a PC evidence CLI reads a JSON evidence bundle and validates schema, safe `evidence_ref`, terminal result type, required materials, field safety, and no success overclaim.
2. KR-B Robot diagnostics: a safe summary alias exposes accepted/blocked intake status while forcing `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
3. KR-C Mobile touchpoint: mobile/web renders a read-only terminal-result material intake panel with safe copy support only when backend-provided safe copy is present.
4. KR-D Product closeout: sprint closeout records evidence boundaries, keeps Objective 5 unchanged unless real verified materials appear, and documents remaining proof gaps.

## Core Product Grabs

The core grab is not another request for missing materials. It is a concrete gate that can consume materials when field owner provides them:

- one bundle in;
- one safe `evidence_ref` across bundle parts;
- strict terminal result type: `delivery`, `dropoff`, or `cancel`;
- required materials listed and checked;
- unsafe raw details rejected;
- overclaim fields rejected;
- safe summary out for diagnostics/mobile;
- controls remain disabled.

## Functional Requirements

### Intake Bundle

The evidence bundle must support:

- `schema=trashbot.verified_terminal_result_material_intake.v1`
- `capability=verified_terminal_result_material_intake`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_intake_gate`
- safe `evidence_ref`
- safe `command_id` when present
- `terminal_result_type` equal to `delivery`, `dropoff`, or `cancel`
- material references for task record, route/elevator material, command lifecycle audit, terminal result payload, and field owner note
- explicit proof flags: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`

### Validation Rules

The intake must fail closed when:

- `evidence_ref` is missing, unsafe, or inconsistent across nested materials.
- `terminal_result_type` is not one of `delivery`, `dropoff`, or `cancel`.
- required material references are missing for the selected result type.
- any source claims `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `route_elevator_field_pass=true`, `hil_pass=true`, or similar success/control overclaim.
- raw artifacts, full JSON dumps, credentials, bearer tokens, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, baudrate values, or WAVE ROVER control details appear in safe fields.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is described as resolved without live reviewer resolution and real hardware materials.

### Summary Artifact

The summary must include only phone-safe fields:

- summary schema and capability.
- intake status: accepted for review, blocked missing material, blocked unsafe field, blocked mismatch, or blocked overclaim.
- safe `evidence_ref` and safe `command_id` when available.
- terminal result type.
- required material status summary.
- blocked reason and next required evidence.
- owner handoff.
- safe copy text if all copied content is sanitized.
- `not_proven`.
- `delivery_success=false`.
- `primary_actions_enabled=false`.
- `safe_to_control=false`.
- evidence boundary.

## Non-Goals

- This sprint does not prove real delivery, real dropoff, real cancel completion, or route/elevator field pass.
- This sprint does not prove real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or external O5 proof.
- This sprint does not prove real iPhone/Android behavior, production app, or real PWA prompt/userChoice.
- This sprint does not prove WAVE ROVER/UART/HIL, real serial, real 2D LiDAR/ToF source/procurement/install/calibration, or PR #5 material closure.
- This sprint does not enable Start Delivery, Confirm Dropoff, Cancel, replay, resubmit, ACK mutation, cursor mutation, or any robot control path.

## Priority And Acceptance

P0:

- PC intake gate must reject unsafe, incomplete, inconsistent, and overclaiming bundles.
- Robot diagnostics must expose the safe summary without control enablement.
- Mobile/web must show read-only status and safe copy without enabling primary actions.
- Product closeout must preserve evidence language and keep Objective 5 unchanged if no real material is accepted.

P1:

- The summary should provide enough owner handoff text for the next field owner to know what material to supply next.
- Docs must explain that this gate consumes terminal result material and is not proof of delivery success.

Acceptance:

- All implementation owners run the fenced commands in `tech-plan.md`.
- Required strings appear across implementation, docs, and sprint records: `verified_terminal_result_material_intake`, `software_proof_docker_verified_terminal_result_material_intake_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- No surface claims true success or control readiness from Docker-only proof.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC evidence CLI, schema validation, test fixtures, evidence interface docs.
- Robot Platform Engineer: diagnostics/status alias, safe summary integration, operator gateway diagnostics tests, interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, safe copy behavior, fixture, UI tests, mobile user flow docs.
- Product Manager / OKR Owner: sprint closeout, OKR/progress log decision, evidence boundary review, no-overclaim acceptance.

## Risks And Evidence Gaps

- The host has Docker only, so all proof remains `software_proof_docker_verified_terminal_result_material_intake_gate`.
- Field owner may not provide real materials; in that case this sprint is a ready intake gate, not a completed delivery result.
- A truthy `delivery_result`, `dropoff_completion`, or `cancel_completion` field can be misleading unless same-`evidence_ref` materials verify it.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and cannot be closed by this sprint.
- Objective 5 should not increase unless real terminal result materials or external proof are supplied and verified.

## Sprint Docs To Create Or Update

Planning phase creates:

- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/pre_start.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/prd.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-plan.md`

Implementation and closeout must later create or update:

- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/side2side_check.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/final.md`
- related `docs/interfaces/` and `docs/product/` files touched by the implementation owners.
- `OKR.md` and `docs/process/okr_progress_log.md` only at Product closeout, and only with conservative evidence boundaries.

