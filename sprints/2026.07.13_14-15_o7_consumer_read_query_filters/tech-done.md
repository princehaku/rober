# Tech Done - O7 Consumer Read Query Filters

## Sprint Type

- sprint_type: epic
- Completed implementation at: 2026-07-13 14:30 CST
- Owner: full-stack-software-engineer
- Proof boundary: `software_proof_o7_consumer_read_query_filters_only`

## Actual Changes

- `pc-tools/workstation/src/shared/contracts.ts`
  - Added O7 consumer task-list query and applied-filter contract types.
  - Added response metadata: `applied_filters`, `filter_semantics=and`, `filtered_result_count`, `o7_consumer_read_query_filters_ready_not_production_proof=true`, and `o7_consumer_read_query_filters_proof_scope=software_proof_o7_consumer_read_query_filters_only`.
- `pc-tools/workstation/src/client/workstationApi.ts`
  - Extended the consumer task-list client URL builder to encode optional `robot_id`, `task_id`, `date`, `status`, `limit`, and `before_started_at_ms` filters.
  - Empty UI filter fields are omitted so default behavior still uses the existing O7 adapter default.
- `pc-tools/workstation/src/server/index.ts`
  - Passed the raw query object into the O7 consumer-read adapter so repeated/array/unknown query shapes can fail closed.
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - Added O7-side query normalization before contacting O6.
  - Safe filters are forwarded to local-loopback O6 `GET /api/o6/consumer/tasks?view=summary&limit=<n>` with AND semantics owned by O6.
  - Unknown keys, repeated/array query values, invalid dates/status/limits/cursors, and URL/path/credential/raw-like filter values fail closed with `invalid_o7_consumer_read_query_filter:<field>` and are not forwarded to O6.
  - Response continues to fix `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, and `robot_control_executed=false`.
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - Added PC UI filters for `robot_id`, `task_id`, `date`, `status`, `limit`, and `before_started_at_ms`.
  - Added list-strategy readback for applied filters, filter semantics, filtered result count, and proof scope.
  - No control, playback, submit, export, or production-cloud actions were added.
- `pc-tools/workstation/test/App.test.ts`
  - Added adapter coverage for safe filtered forwarding to O6 and unsafe query fail-closed before fetch.
  - Added UI coverage proving operator-entered filters are encoded in the O7 workstation API request and rendered back as applied values.
- `docs/interfaces/o7_realtime_operator_console.md`
  - Documented the O7 consumer-read query filter contract, fail-closed behavior, loopback-only boundary, and rejected claims.

## Verification Results

- `cd pc-tools/workstation && npm run test`
  - Passed: `Test Files 3 passed (3)`, `Tests 494 passed (494)`.
- `cd pc-tools/workstation && npm run build`
  - Passed: `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`.
  - Vite emitted the existing large chunk warning for `dist/assets/index-*.js`; build completed successfully.
- `cd pc-tools/workstation && npm run lint`
  - Passed: `eslint .`.
- `git diff --check -- ...`
  - Passed for the allowed source/docs/test files and this sprint directory.

## Failure Localization and Fixes

- First `npm run build` failed on TypeScript strictness:
  - `Date.UTC(year, month - 1, day)` inferred possibly undefined date parts.
  - New adapter test fetch mock had no typed argument, so `mock.calls[0][0]` was inferred as unavailable.
  - Fixed by parsing explicit date parts and typing the mocked fetch argument.
- First `npm run lint` failed on an unused typed fetch argument in the new test.
  - Fixed with `void url` while preserving mock call tuple typing.
- After fixes, `npm run test`, `npm run build`, and `npm run lint` all passed.

## Remaining Risk

- This proves only the O7 PC workstation software path and local-loopback O6 query forwarding contract.
- It does not prove production cloud, production DB/queue, real robot data, real phone/browser behavior, route execution, delivery/operator acceptance, HIL, safe-to-control, O5 external evidence, real annotation/export, or long-term query capacity.
- O6 remains the owner of actual task-list AND filtering semantics; O7 validates and forwards safe query values and displays applied metadata.

## Fixed Rejected Claims

- production cloud: not proven
- real robot data: not proven
- route execution: not proven
- delivery: not proven
- HIL: not proven
- safe-to-control: not proven
- control/playback/submit/export enablement: not enabled
