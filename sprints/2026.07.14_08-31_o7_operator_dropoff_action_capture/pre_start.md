# Pre Start - O7 Operator Dropoff Action Capture

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/`
- Created at: 2026-07-14 08:31 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Sprint status: planning ready, implementation not started
- Proof boundary: `software_proof_o6_o7_operator_dropoff_action_capture_only`

## User Value And North Star

North Star remains: ordinary users can hand trash to the robot, trigger or confirm the dropoff workflow from a human-facing surface, and later prove what happened without knowing ROS2, SSH, serial devices, cloud internals, or hardware debug tools.

This sprint creates the PC/O7 operator action entry point that a future real operator session can use to capture dropoff acceptance against a selected `task_id`. The immediate value is not delivery success; it is a safe, task-scoped action-write path that records a bounded operator dropoff acceptance request into the O6 archive and shows an O7 receipt.

## Previous Evidence And Routing Decision

Current `OKR.md` shows O5 at about `85%`, lower than O1 about `94%` and O6/O7 about `93%`.

The latest O5 sprint `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/final.md` accepted only a synthetic/local operator dropoff acceptance gate. It explicitly rejected real operator action, delivery success, live route execution, HIL, safe-to-control, production cloud, 4G/SIM, true phone/browser, `/cmd_vel`, `/api/base/manual`, NavigateToPose, and WAVE ROVER UART evidence.

Product direction for this sprint: do not repeat the O5 gate as another local wrapper. O5 can score next only with same-window live route/HIL/operator evidence or success-class production/cloud evidence. Current automation does not have real hardware, real 4G, real cloud production success, or a real operator/browser session, so this sprint pivots to a distinct O7/O6 action-write path.

## Scope

Create planning for a PC/O7 selected-task operator dropoff action capture endpoint and UI receipt:

- O6 event type: `operator.dropoff_acceptance`
- O7 endpoint: `POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>`
- O7 receipt schema: `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`
- Proof boundary: `software_proof_o6_o7_operator_dropoff_action_capture_only`

The successful local/mock proof may claim only:

- selected-task operator action request construction
- O6 local archive event write and readback receipt
- O7 UI receipt display
- fail-closed validation for unsafe claims and non-loopback inputs

## Rejected Claims

The sprint must keep these fields fixed false in local/mock proof:

- `real_operator_action_proven=false`
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

This sprint must not claim real operator action, delivery success, route execution, HIL, safe-to-control, production cloud, 4G/SIM, real browser/phone session, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.

## Owner Routing

- `full-stack-software-engineer` owns implementation, tests, docs sync, and `tech-done.md`.
- `product-okr-owner` owns Product acceptance, `side2side_check.md`, `final.md`, OKR direction judgment, and no-repeat closeout after implementation.
- No parallel engineer is required now. The endpoint consumes existing O6 archive event semantics and existing O7 selected-task patterns; if O6 event whitelist changes are needed, they stay inside the same Full-Stack API/UI scope.

## Sprint Document Plan

Create now:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Do not create during planning:

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Implementation owner must create `tech-done.md` only after code, tests, docs sync, and verification are complete. Product acceptance may later create `side2side_check.md` and `final.md`.

## Expected OKR Result

Expected result after implementation: O5 remains about `85%`, O1 remains about `94%`, O6/O7 remain about `93%`, main percentages unchanged, KR `不归档`.

This sprint is useful because it gives future real operator action a safe capture entry point; it is not mission-grade evidence by itself.
