# Tech Plan - O7 Consumer Event Append

## Summary

Add a PC/O7 selected-task local/mock `mission event append` action that validates a mission event in the Node adapter, forwards it to O6 `POST /api/o6/archive/events`, and returns a fail-closed receipt. This is a software-only archive action-write increment, not production cloud, robot control, route execution, delivery, HIL, or safe-to-control proof.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: O5 at about `85%`.
2. This sprint does not target O5.
3. Reason: the latest O5 evidence sprint `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` closed on `blocked_http_status_not_success_class`. Without success-class public endpoint, production DB/queue, worker cutover, OSS/CDN, 4G/SIM, or real phone/browser evidence, another O5 sprint would repeat the same blocker. O1/O3 route execution/HIL also requires explicit operator approval and current live evidence that this automation cannot trigger. Therefore this Epic switches to a non-repeating O7/O6 action-write increment tied to `task_id` mission evidence. Expected OKR result remains flat and `不归档`.

## Owner

- Primary owner: `full-stack-software-engineer`.
- Product acceptance owner: `product-okr-owner`.
- Parallel owners: none. This is a single-owner PC/O7 adapter/UI/API/test slice using an existing O6 endpoint.

## Allowed Implementation File Scope

Implementation may modify only these files unless a blocker is returned for Product decision:

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_16-16_o7_consumer_event_append/tech-done.md`

Do not modify `OKR.md`, `docs/process/okr_progress_log.md`, historical sprint files, hardware files, ROS/Nav files, or O6 archive backend code in the first implementation pass. The existing O6 `POST /api/o6/archive/events` contract should be consumed, not redefined.

## Existing Contract Facts

- O6 endpoint: `POST /api/o6/archive/events`.
- O6 event append is task-bound and idempotent by `task_id + event_id`.
- O6 accepts local/mock event types currently allowed by the archive contract, including `operator.note`, `task.failure`, `task.recovery`, `route.frame`, `route.pose`, `elevator.door_state`, `elevator.floor_evidence`, and `perception.detected_object`.
- O6 receipt already includes local/mock fixed false fields and `archive_event_written`; O7 must validate those before surfacing success.

## Planned O7 API

Endpoint:

```text
POST /api/o7/consumer-read/tasks/:taskId/events/append?baseUrl=<local-loopback-url>
```

Request body:

```ts
interface O7ConsumerMissionEventAppendRequestBody {
  robot_id: string;
  task_id?: string;
  event_id: string;
  event_type:
    | "operator.note"
    | "task.failure"
    | "task.recovery"
    | "route.frame"
    | "route.pose"
    | "elevator.door_state"
    | "elevator.floor_evidence"
    | "perception.detected_object";
  occurred_at_ms: number;
  summary?: string;
  severity?: "info" | "warning" | "error";
  evidence_ref?: string;
  evidence_refs?: string[];
  metadata?: Record<string, string | number | boolean | null>;
}
```

Adapter forwarding body:

```ts
{
  robot_id,
  task_id: selectedTaskId,
  events: [
    {
      event_id,
      event_type,
      occurred_at_ms,
      summary,
      severity,
      evidence_refs,
      metadata,
    },
  ],
}
```

Receipt:

```ts
interface O7ConsumerMissionEventAppendResult {
  schema: "trashbot.pc_tools_workstation.o7_consumer_mission_event_append_result.v1";
  append_status: "local_mock_event_written" | "local_mock_event_updated" | "fail_closed";
  source_base_url: string;
  remote_endpoint: "/api/o6/archive/events";
  remote_schema: string;
  requested_task_id: string;
  o6_http_status: number | null;
  task_id: string;
  robot_id: string;
  event_id: string;
  event_type: string;
  occurred_at_ms: number | null;
  evidence_refs_consumed: string[];
  write_status: "created" | "updated" | "blocked_not_proven";
  duplicate: boolean;
  created_count: number;
  updated_count: number;
  archive_event_written: boolean;
  events_written_count: number;
  event_summary: Record<string, unknown>;
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
  connects_cloud_production: false;
  robot_control_executed: false;
  route_execution_success: false;
  hil_pass: false;
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
}
```

## Fail-Closed Rules

- Reject non-local `baseUrl`; only loopback HTTP is allowed.
- Reject missing or mismatched `task_id`.
- Reject missing `robot_id`, `event_id`, `event_type`, `occurred_at_ms`, and safe `evidence_ref`/`evidence_refs`.
- Reject unsupported `event_type`, invalid timestamp, oversized metadata, unsafe strings, raw payload content, complete URLs with credentials, local absolute paths, ROS topic/control strings, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, and dangerous true fields.
- Reject O6 responses with schema/source/proof-status mismatch, `archive_event_written !== true`, task/robot/event identity mismatch, unsupported `write_status`, missing `event_summary`, or any fixed false field not equal to false.

## Fixed False Fields

The implementation and tests must assert these fields remain false:

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`
- `real_cloud_db_connected=false` if surfaced
- `real_oss_connected=false` if surfaced

The sprint must explicitly state that it does not touch `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or primary actions.

## UI Requirements

- Add one compact selected-task action in the existing O7 fixture/consumer panel for appending a local/mock mission event.
- Use the selected `task_id` from the consumer detail path.
- Show receipt fields: status, `event_id`, `event_type`, `archive_event_written`, write status, created/updated counts, and fixed false fields.
- Do not add marketing copy or claim production/robot readiness.

## Verification Commands

Run from repository root after implementation:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_16-16_o7_consumer_event_append
```

Recommended targeted anchors after implementation:

```bash
rg -n "o7_consumer_mission_event_append_result|archive/events|local_mock_event_written|local_mock_event_updated|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|connects_cloud_production=false|robot_control_executed=false|不归档" pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_16-16_o7_consumer_event_append
```

## Acceptance Evidence Required In `tech-done.md`

The implementing owner must return:

1. Actual changed files.
2. `npm run test`, `npm run build`, `npm run lint`, and scoped `git diff --check` output.
3. Positive write test showing O7 forwarded one safe event to O6 `POST /api/o6/archive/events` and returned `local_mock_event_written`.
4. Idempotent update test showing the same `event_id` returns `local_mock_event_updated`.
5. Fail-closed tests for unsafe base URL, task mismatch, unsafe evidence refs, unsupported event type, dangerous true claims, and bad O6 receipt.
6. Remaining risk and proof boundary.

## Risk Boundary

Accepted proof: O7 selected-task local/mock mission event append software proof only.

Rejected proof: production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, real robot data, route execution, delivery success, operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or primary actions.

OKR result expected after successful implementation: O5 remains about `85%`, O1 remains about `94%`, O6/O7 remain about `93%`, main percentages no adjustment, KR `不归档`.
