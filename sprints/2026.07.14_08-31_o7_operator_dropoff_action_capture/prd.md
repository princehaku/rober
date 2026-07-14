# PRD - O7 Operator Dropoff Action Capture

## Product Summary

Build a local/mock PC/O7 selected-task action-write path that lets an operator request a dropoff acceptance capture for a specific task, writes a safe O6 archive event, and shows a receipt in the O7 workstation.

This is a user-touchpoint increment for the operator acceptance chain. It does not prove that a real human accepted a real delivery; it only creates the safe product entry point needed to collect that evidence in a future live session.

## User Value And North Star

The user-facing goal is to make the delivery handoff auditable. A normal operator should eventually be able to confirm "trash was dropped off" from a PC/operator surface, and the system should preserve that action as task-scoped evidence that later delivery-success gates can evaluate.

This sprint moves one step toward the north star by making the operator action path explicit, bounded, task-scoped, and fail-closed.

## OKR Mapping And Direction Judgment

- Lowest objective: O5 at about `85%`.
- Direction judgment: adjust this sprint away from O5 local gate packaging and toward O7/O6 action-write.
- Reason: `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/final.md` already closed the O5 operator dropoff gate as synthetic/local proof only and warned not to repeat local wrappers. O5 now requires same-window live route/HIL/operator evidence or success-class production/cloud evidence.
- Current available path: O7/O6 selected-task action-write, because it creates an operator action entry point without pretending to be live evidence.
- Expected OKR result: flat. No KR archival.

## KR Handling

No KR is completed or archived in this planning sprint.

Current KR attention should stay on:

- O5: production/cloud success evidence or same-window live route + terminal result + operator/dropoff + HIL/safe-to-control evidence.
- O7/O6: selected-task operator action capture as a prerequisite surface, not as mission proof.

Historical record after future implementation should be placed in that sprint's `final.md` and, if accepted, summarized in `OKR.md` and `docs/process/okr_progress_log.md` by Product. This planning-only sprint does not modify those files.

## Core Requirement

Add a PC/O7 action for a selected consumer task:

```text
POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>
```

The O7 adapter must construct a safe O6 event write:

- O6 endpoint: `POST /api/o6/archive/events`
- O6 event type: `operator.dropoff_acceptance`
- Event must be task-bound and robot-bound.
- Event payload must be safe metadata only.
- O7 receipt schema must be `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`.
- Proof boundary must be `software_proof_o6_o7_operator_dropoff_action_capture_only`.

## Success Criteria

Successful implementation proves only:

1. O7 selected-task request construction from a loaded task detail.
2. Local-loopback O6 archive event write/readback with `event_type=operator.dropoff_acceptance`.
3. O7 receipt display in the selected-task UI.
4. Fail-closed handling for unsafe URL, task mismatch, unsafe evidence refs, unsupported event type, dangerous true fields, and invalid O6 receipt.

## Fixed False Fields

The receipt and tests must keep the current local/mock proof fixed false:

- `real_operator_action_proven=false`
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

If implementation needs additional false fields for compatibility, they may be added, but these seven fields are mandatory.

## Non-Goals

This sprint does not:

- prove real operator action
- prove delivery success
- execute route movement
- call `/cmd_vel`
- call `/api/base/manual`
- send NavigateToPose
- touch WAVE ROVER UART
- prove HIL or safe-to-control
- connect production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, or real operator session
- consume O5 gate artifact for OKR credit

## Product Acceptance

Product can accept implementation only if:

- Full-Stack produces `tech-done.md` with actual changed files, validation outputs, failed-test repair notes if any, and remaining risk.
- O6 whitelist is safe and fail-closed for `operator.dropoff_acceptance`.
- O7 endpoint is local-loopback only.
- O7 receipt schema matches `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`.
- Fixed false fields are visible in tests and UI receipt.
- Docs under `docs/interfaces/` and `docs/product/` are synchronized.

## Responsibility

- Primary implementation owner: `full-stack-software-engineer`
- Product acceptance owner: `product-okr-owner`
- Consulted only if live execution/HIL scope appears: `robot-algorithm-engineer`, `rober-hardware-engineer`, `robot-software-engineer`

## Risks And Evidence Gaps

- Risk: this could be mistaken for real operator acceptance. Mitigation: fixed `real_operator_action_proven=false`, explicit receipt wording, and fail-closed true-claim tests.
- Risk: O6 event type whitelist could become too broad. Mitigation: allow only `operator.dropoff_acceptance` for this action path and reject unknown fields/dangerous true claims.
- Risk: UI could imply primary action readiness. Mitigation: receipt display must include fixed false fields and must not enable robot control, route execution, or delivery-success claims.
- Evidence gap after this sprint: still no same-window live route execution, real terminal result, real operator acceptance, HIL pass, safe-to-control, or success-class production/cloud evidence.

## Sprint Documents

This planning task creates:

- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/pre_start.md`
- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/prd.md`
- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/tech-plan.md`

Implementation must later create:

- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/tech-done.md`

Product acceptance may later create:

- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/side2side_check.md`
- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/final.md`
