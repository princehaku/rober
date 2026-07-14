# Side-by-Side Check - O7 Consumer Event Append

## Sprint Type

sprint_type: epic

## Product Acceptance Decision

Status: accepted with proof boundary.

Product accepts `sprints/2026.07.13_16-16_o7_consumer_event_append/` as O7/O6 selected-task local/mock mission event append software proof only. The accepted proof boundary is `software_proof_o7_o6_consumer_mission_event_append_only`.

This does not change the main OKR percentages. O5 remains about `85%`, O1 remains about `94%`, and O6/O7 remain about `93%`. 本轮 KR `不归档`.

## User Value And North Star

User value: the PC operator can add a bounded mission event to the selected task, such as an operator note or route observation, without leaving the O7 selected-task workflow or using raw O6 tooling.

North star fit: this supports the durable trash-delivery evidence chain by making task events observable and replayable. It is not a delivery result, robot-control action, production-cloud proof, route execution record, or HIL acceptance.

## Requirement Versus Evidence

| Requirement | Product check | Acceptance result |
| --- | --- | --- |
| Selected-task O7 action writes one mission event | `tech-done.md` records `POST /api/o7/consumer-read/tasks/:taskId/events/append?baseUrl=<local-loopback-url>` | Accepted |
| O7 forwards only to O6 event archive | Adapter fixed to `POST /api/o6/archive/events` | Accepted |
| Receipt schema is explicit | `trashbot.pc_tools_workstation.o7_consumer_mission_event_append_result.v1` | Accepted |
| Success statuses remain local/mock | `local_mock_event_written` and `local_mock_event_updated` are covered | Accepted |
| Unsafe requests fail closed | Tests cover unsafe base URL, task mismatch, unsafe evidence ref, unsupported event type, dangerous true claim, and bad O6 receipt | Accepted |
| Fixed false fields remain false | `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`, `real_cloud_db_connected=false`, `real_oss_connected=false` | Accepted |
| Verification is sufficient for software proof | Workstation `Tests 498 passed (498)`, build/lint/scoped diff checks passed after TypeScript guard fix | Accepted |

## Accepted Proof Boundary

Accepted proof boundary: `software_proof_o7_o6_consumer_mission_event_append_only`.

Accepted material facts:

- O7 exposes selected-task `mission event append`.
- O7 only accepts local-loopback `baseUrl`.
- O7 forwards exactly to O6 `archive/events`.
- O7 returns `o7_consumer_mission_event_append_result` with `local_mock_event_written` or `local_mock_event_updated`.
- O7/O6 can write or idempotently update a local/mock event tied to one selected `task_id`.

## Rejected Claims

Product explicitly rejects this sprint as proof of production cloud, production DB/queue, real cloud DB, real OSS, OSS/CDN, 4G/SIM, real robot data, real phone/browser operation, route execution, delivery/operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, primary action enablement, or O5 external production evidence.

Safety and mission fields remain fixed false: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`, `real_cloud_db_connected=false`, `real_oss_connected=false`.

## OKR Mapping And Direction

- O5 remains the lowest Objective at about `85%`, but this sprint correctly does not repeat the O5 `blocked_http_status_not_success_class` blocker from `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`.
- O6 gains a bounded local/mock event append consumer path for archive event semantics, but not production persistence.
- O7 gains a selected-task action-write workflow, but not live route execution, delivery, HIL, or production evidence.
- Direction judgment: continue O7/O6 only when the next slice produces a new mission artifact or non-repeating action/write result; otherwise prioritize explicit operator-approved current live HIL/current route evidence or real production/cloud evidence.

## Verification Evidence

Evidence from `tech-done.md`:

- `cd pc-tools/workstation && npm run test`: `Test Files 3 passed (3)`, `Tests 498 passed (498)`.
- Re-run after TypeScript guard fix: `Test Files 3 passed (3)`, `Tests 498 passed (498)`.
- `cd pc-tools/workstation && npm run build`: first failed on TS18048 around possibly undefined O6 event/firstEvent; explicit guards were added and the rerun passed, with only the existing Vite large chunk warning.
- `cd pc-tools/workstation && npm run lint`: passed.
- Scoped `git diff --check`: passed.
- Anchor check found `archive/events`, `local_mock_event_written`, `local_mock_event_updated`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, and `不归档`.

## Remaining Risk And Next Evidence

Remaining risk: this is local/mock software proof and cannot count as route execution, delivery, production cloud, real robot data, HIL, or safe-to-control. The Vite large chunk warning is pre-existing and non-blocking for this Product acceptance.

Next evidence required: explicit operator-approved current live HIL/current route execution evidence, or success-class real production/cloud evidence such as public endpoint success, production DB/queue, worker cutover, OSS/CDN, 4G/SIM, or real phone/browser proof. If those remain unavailable, the next O7/O6 slice must consume a new mission artifact or real/mock delivery result rather than repeat query/readback wrappers.
