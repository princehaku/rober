# Side-by-Side Check - O7 Delivery Result Intake

## Sprint Type

sprint_type: epic

## Product Acceptance Decision

Status: accepted with proof boundary.

Product accepts `sprints/2026.07.13_17-17_o7_delivery_result_intake/` as O7/O6 selected-task local/mock delivery result intake software proof only. The accepted proof boundary is `software_proof_o7_o6_consumer_delivery_result_intake_only`.

This does not change the main OKR percentages. O5 remains about `85%`, O1 remains about `94%`, and O6/O7 remain about `93%`. 本轮 KR `不归档`.

## User Value And North Star

User value: the PC operator can write a bounded delivery result evidence request against the currently selected task, then see a fail-closed receipt without leaving the O7 workflow or calling raw O6 APIs.

North star fit: this is closer to the trash-delivery evidence chain than a query/readback wrapper because it writes delivery result material into the O6 field-evidence path. It is still not delivery success, route execution, production cloud proof, HIL acceptance, or safe-to-control evidence.

## Requirement Versus Evidence

| Requirement | Product check | Acceptance result |
| --- | --- | --- |
| Selected-task O7 action writes delivery result material | `tech-done.md` records `POST /api/o7/consumer-read/tasks/<task_id>/delivery-result/intake?baseUrl=<local-loopback-url>` | Accepted |
| O7 forwards only to fixed O6 field-evidence intake | Adapter fixed to `POST /api/o6/archive/field-evidence` | Accepted |
| Receipt schema is explicit | `trashbot.pc_tools_workstation.o7_consumer_delivery_result_intake_result.v1` | Accepted |
| Success statuses remain local/mock | `local_mock_delivery_result_written` and `local_mock_delivery_result_updated` are covered | Accepted |
| Unsafe requests fail closed | Tests cover unsafe input, bad O6 receipt, task/robot/result mismatch, and false-field mismatch | Accepted |
| O6 write evidence is visible | Receipt verifies `field_evidence_written=true` and O6 `write_status=created|updated` before O7 returns success | Accepted |
| Fixed false fields remain false | `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`, `real_cloud_db_connected=false`, `real_oss_connected=false` | Accepted |
| Verification is sufficient for software proof | Workstation `Test Files 3 passed (3)`, `Tests 501 passed (501)`, build/lint/scoped diff checks passed | Accepted |

## Accepted Proof Boundary

Accepted proof boundary: `software_proof_o7_o6_consumer_delivery_result_intake_only`.

Accepted material facts:

- O7 exposes selected-task `delivery-result/intake`.
- O7 only accepts local-loopback `baseUrl`.
- O7 forwards exactly to O6 `archive/field-evidence`.
- O7 returns `o7_consumer_delivery_result_intake_result` with `local_mock_delivery_result_written` or `local_mock_delivery_result_updated`.
- O7/O6 can write or idempotently update local/mock delivery result evidence tied to one selected `task_id`.

## Rejected Claims

Product explicitly rejects this sprint as proof of production cloud, production DB/queue, real cloud DB, real OSS, OSS/CDN, 4G/SIM, real robot data, real phone/browser operation, route execution, delivery/operator acceptance, real delivery success, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, primary action enablement, or O5 external production evidence.

Safety and mission fields remain fixed false: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`, `real_cloud_db_connected=false`, `real_oss_connected=false`.

## OKR Mapping And Direction

- O5 remains the lowest Objective at about `85%`, but this sprint correctly does not repeat the O5 `blocked_http_status_not_success_class` blocker from `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`.
- O6 gains a bounded local/mock delivery result evidence intake path through `field-evidence`, but not production persistence or production query capacity.
- O7 gains a selected-task action-write workflow for delivery result material, but not live route execution, delivery success, HIL, or production evidence.
- Direction judgment: continue only if the next slice produces explicit operator-approved current live HIL/current route evidence, real production/cloud evidence, or a stronger same-task mission artifact. Do not repeat query/readback wrappers.

## Verification Evidence

Evidence from `tech-done.md`:

- `cd pc-tools/workstation && npm run test`: `Test Files 3 passed (3)`, `Tests 501 passed (501)`.
- `cd pc-tools/workstation && npm run build`: passed with only the existing Vite large chunk warning.
- `cd pc-tools/workstation && npm run lint`: passed.
- Scoped `git diff --check`: passed.
- Implementation evidence includes `field_evidence_written=true`, `software_proof_o7_o6_consumer_delivery_result_intake_only`, `local_mock_delivery_result_written`, `local_mock_delivery_result_updated`, and all fixed false fields.

## Remaining Risk And Next Evidence

Remaining risk: this is local/mock software proof and cannot count as route execution, delivery success, production cloud, real robot data, HIL, or safe-to-control. The Vite large chunk warning is pre-existing and non-blocking for this Product acceptance.

Next evidence required: explicit operator-approved current live HIL/current route execution evidence, or success-class real production/cloud evidence such as public endpoint success, production DB/queue, worker cutover, OSS/CDN, 4G/SIM, or real phone/browser proof. If those remain unavailable, O7/O6 must consume a stronger same-task mission artifact instead of repeating readback/query wrapper work.
