# Tech Done - O7 Consumer Event Append

## Sprint Type

sprint_type: epic

## Actual Changes

- `pc-tools/workstation/src/shared/contracts.ts`
  - Added `O7ConsumerMissionEventAppendRequestBody`, `O7ConsumerMissionEventAppendResult`, allowed event type union, and route catalog entry for `POST /api/o7/consumer-read/tasks/<task_id>/events/append?baseUrl=<local-loopback-url>`.
- `pc-tools/workstation/src/client/workstationApi.ts`
  - Added `postO7ConsumerMissionEventAppend()` client helper and fixed `/events/append` suffix.
- `pc-tools/workstation/src/server/index.ts`
  - Added Express route `POST /api/o7/consumer-read/tasks/:taskId/events/append`.
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - Added O7 mission event append adapter that allows only HTTP local-loopback `baseUrl`, validates path/body `task_id` consistency, normalizes one safe event, and forwards only `POST /api/o6/archive/events`.
  - Added fail-closed validation for unsupported event types, invalid timestamps, missing safe evidence refs, oversized metadata, unsafe/raw/base64/control strings, dangerous true fields, bad O6 schema/source/proof/status, bad identities, bad write status, missing event summary, and fixed false-field mismatch.
  - Success receipt schema is `trashbot.pc_tools_workstation.o7_consumer_mission_event_append_result.v1`; statuses are `local_mock_event_written` and `local_mock_event_updated`.
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - Added compact selected-task local/mock mission event append control beside the existing consumer-detail action area.
  - UI uses selected task `task_id`, default detail event/evidence refs, and displays receipt status, event identity, `archive_event_written`, write counts, O6 schema/source, evidence refs, and fixed false fields.
- `pc-tools/workstation/test/catalog.test.ts`
  - Added O6 event endpoint harness capture.
  - Covered success write, idempotent update, unsafe base URL, task mismatch, unsafe evidence ref, unsupported event type, dangerous true claim, and bad O6 receipt fail-closed.
- `pc-tools/workstation/test/App.test.ts`
  - Added UI fixture result and flow assertions for disabled-before-detail, event append POST path, receipt schema/status, archive endpoint, write receipt, and fixed false fields.
- `docs/interfaces/o7_realtime_operator_console.md`
  - Documented the O7 mission event append endpoint, allowed forwarding path, validation rules, receipt schema, and proof boundary.
- `docs/product/pc_tools_workstation.md`
  - Updated workstation product boundary and selected-task UI section for mission event append.

## Verification Results

- `cd pc-tools/workstation && npm run test`
  - Initial run passed: `Test Files 3 passed (3)`, `Tests 498 passed (498)`.
  - Re-run after TypeScript guard fix passed: `Test Files 3 passed (3)`, `Tests 498 passed (498)`.
- `cd pc-tools/workstation && npm run build`
  - First run failed on TypeScript nullability for O6 `events_written[0]`.
  - Fixed by explicitly guarding the returned event before reading `event_id`, `event_type`, `occurred_at_ms`, and `evidence_refs`.
  - Re-run passed: `tsc`, `vite build`, and server `tsc` completed.
  - Existing Vite warning remained: chunk larger than 500 kB after minification.
- `cd pc-tools/workstation && npm run lint`
  - Passed: `eslint .`
- Scoped diff check:
  - `git diff --check -- ... sprints/2026.07.13_16-16_o7_consumer_event_append`
  - Passed with no output.
- Anchor scan:
  - `rg -n "o7_consumer_mission_event_append_result|archive/events|local_mock_event_written|local_mock_event_updated|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|connects_cloud_production=false|robot_control_executed=false|不归档" ...`
  - Passed; anchors are present in code, tests, docs, and sprint materials.

## Deviation / Failure Location

- Build initially failed because TypeScript could not prove `sampleObjectArray(remote.events_written, 2)[0]` and `validation.eventsWritten[0]` were defined even after a length check.
- Root cause: array index access remains possibly undefined under current TypeScript settings.
- Fix: added explicit `if (!event)` / `if (!firstEvent)` guards and returned fail-closed reason `o6_event_written_count_mismatch`.

## Remaining Risk

- Proof boundary is O7/O6 selected-task local/mock mission event append software proof only.
- This does not prove production cloud, real cloud DB, real OSS, real robot data, route execution, delivery/operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, 4G/SIM, or real phone/browser operation.
- Product acceptance still needs to close `side2side_check.md` and `final.md`; this implementation intentionally did not create those files.
