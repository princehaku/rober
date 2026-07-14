# Tech Plan - O7 Operator Dropoff Action Capture

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/`
- Primary owner: `full-stack-software-engineer`
- Product owner: `product-okr-owner`
- Scope type: PC/O7 selected-task action-write with O6 archive event receipt
- Proof boundary: `software_proof_o6_o7_operator_dropoff_action_capture_only`

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5, about `85%`.
- 本 sprint 是否直接针对最低 Objective：否。
- 理由：最新 O5 sprint `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/final.md` 已把 operator dropoff acceptance gate 接成 synthetic/local software proof，并明确不要再围绕该 gate 做 local wrapper。O5 下一步需要 same-window live route/HIL/operator evidence 或 success-class production/cloud evidence；当前自动化环境没有真实硬件、真实 4G、真实 cloud production success 或真实 operator/browser session。
- 本 sprint 的次优可推进路径：转向 O7/O6 selected-task action-write，增加 `operator.dropoff_acceptance` 的安全写入入口和 O7 receipt，为未来真实 operator action 提供入口，但不消费 O5 gate artifact，不声明 O5 计分。
- final.md 收口时必须复核：O5 仍不可重复包装；本 sprint 只接受为 local/mock software proof，O5/O6/O7 百分比预期保持 flat，KR `不归档`。

## Contract Summary

O6 event type:

```text
operator.dropoff_acceptance
```

O7 endpoint:

```text
POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>
```

O7 receipt schema:

```text
trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1
```

The endpoint must be local-loopback only and selected-task only. It must write a safe O6 archive event through `POST /api/o6/archive/events` and return a fail-closed O7 receipt.

## Planned Request Shape

Implementation may adjust names if existing contracts require it, but the contract must stay equivalent and fail-closed:

```ts
interface O7OperatorDropoffActionCaptureRequestBody {
  robot_id: string;
  task_id?: string;
  event_id: string;
  occurred_at_ms: number;
  operator_action_id?: string;
  operator_display_name?: string;
  evidence_ref?: string;
  evidence_refs?: string[];
  summary?: string;
  metadata?: Record<string, string | number | boolean | null>;
}
```

Adapter forwarding body to O6:

```ts
{
  robot_id,
  task_id: selectedTaskId,
  events: [
    {
      event_id,
      event_type: "operator.dropoff_acceptance",
      occurred_at_ms,
      summary,
      evidence_refs,
      metadata: {
        operator_action_id,
        operator_display_name,
        proof_boundary: "software_proof_o6_o7_operator_dropoff_action_capture_only",
        real_operator_action_proven: false,
      },
    },
  ],
}
```

## Planned Receipt Shape

Receipt must include at least:

```ts
interface O7OperatorDropoffActionCaptureResult {
  schema: "trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1";
  proof_boundary: "software_proof_o6_o7_operator_dropoff_action_capture_only";
  capture_status:
    | "local_mock_operator_dropoff_acceptance_event_written"
    | "local_mock_operator_dropoff_acceptance_event_updated"
    | "fail_closed";
  local_loopback_only: true;
  source_base_url: string;
  remote_endpoint: "/api/o6/archive/events";
  requested_task_id: string;
  task_id: string;
  robot_id: string;
  event_id: string;
  event_type: "operator.dropoff_acceptance";
  occurred_at_ms: number | null;
  write_status: "created" | "updated" | "blocked_not_proven";
  archive_event_written: boolean;
  events_written_count: number;
  event_summary: Record<string, unknown>;
  evidence_refs_consumed: string[];
  real_operator_action_proven: false;
  delivery_success: false;
  route_execution_success: false;
  safe_to_control: false;
  hil_pass: false;
  robot_control_executed: false;
  connects_cloud_production: false;
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
}
```

For anchor checks and closeout wording, docs and implementation should include exact fixed-false strings:

- `real_operator_action_proven=false`
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## Implementation Plan

1. O6 archive event whitelist:
   - Add or confirm safe whitelist support for `operator.dropoff_acceptance`.
   - Keep `POST /api/o6/archive/events` fail-closed for unsupported event types, unsafe refs, raw payloads, absolute paths, credentials, command strings, and dangerous true claims.
   - Add/update tests proving `operator.dropoff_acceptance` can be written and true claims are rejected.
2. O7 adapter/server:
   - Add `POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request`.
   - Validate local-loopback `baseUrl`, path/body `task_id` consistency, `robot_id`, `event_id`, `occurred_at_ms`, optional operator metadata, and safe evidence refs.
   - Forward exactly one O6 `POST /api/o6/archive/events` request with `event_type=operator.dropoff_acceptance`.
   - Validate O6 response schema/source/proof status, task/robot/event identity, `archive_event_written`, `write_status`, `event_summary`, and fixed false fields.
   - Return `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`.
3. O7 UI receipt:
   - Add a compact selected-task operator dropoff action in the existing consumer detail surface.
   - Require a loaded selected task before action.
   - Show capture status, `event_id`, `event_type`, O6 write status, archive event written count, fixed false fields, blocked reasons, and not-proven list.
   - Do not show production, control, route, HIL, or delivery-ready claims.
4. Docs and sprint record:
   - Update O6/O7 interface docs and PC workstation product docs.
   - Implementation owner must create `tech-done.md` with actual changes, verification logs, failure repair if any, and remaining risk.

## File Scope For Implementation

Allowed implementation files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture/tech-done.md`

Do not modify:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- hardware, WAVE ROVER, UART, Nav2, launch, Docker, or route execution files
- historical sprint directories
- `side2side_check.md` or `final.md` before implementation acceptance

## Fail-Closed Rules

The owner must reject or return `capture_status=fail_closed` for:

- non-loopback or non-HTTP `baseUrl`
- URL credentials, query/hash smuggling, or production/cloud URL
- path/body `task_id` mismatch
- missing `robot_id`, `event_id`, `occurred_at_ms`, or selected task context
- unsupported or overridden `event_type`
- unsafe `evidence_ref` / `evidence_refs`
- raw payloads, absolute paths, complete URLs, credentials, tokens, bearer strings, base64-like blobs, traceback-like text, ROS topic/control command strings, `/cmd_vel`, `/api/base/manual`, NavigateToPose, serial/UART, or WAVE ROVER wording
- any request or O6 response claiming `real_operator_action_proven=true`, `delivery_success=true`, `route_execution_success=true`, `safe_to_control=true`, `hil_pass=true`, `robot_control_executed=true`, or `connects_cloud_production=true`
- O6 schema/source/proof mismatch, identity mismatch, missing `archive_event_written`, unsupported `write_status`, missing `event_summary`, or fixed false fields not equal to false

## Acceptance Commands For Implementation Owner

Run from repository root after implementation:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

```bash
cd pc-tools/workstation && npm run test
```

```bash
cd pc-tools/workstation && npm run build
```

```bash
cd pc-tools/workstation && npm run lint
```

```bash
rg -n "operator/dropoff-acceptance/request|operator.dropoff_acceptance|o7_operator_dropoff_action_capture_result|software_proof_o6_o7_operator_dropoff_action_capture_only|real_operator_action_proven=false|delivery_success=false|route_execution_success=false|safe_to_control=false|hil_pass=false|robot_control_executed=false|connects_cloud_production=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src pc-tools/workstation/test docs/interfaces docs/product sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture
```

If any command fails, the owner must diagnose, fix, and rerun before returning.

## Product Planning Self-Check

Product planning must run:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|operator.dropoff_acceptance|o7_operator_dropoff_action_capture_result|software_proof_o6_o7_operator_dropoff_action_capture_only|real_operator_action_proven=false|delivery_success=false|safe_to_control=false|full-stack-software-engineer" sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture
```

```bash
git diff --check -- sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture
```

```bash
find sprints/2026.07.14_08-31_o7_operator_dropoff_action_capture -maxdepth 1 -type f -print | sort
```

## Acceptance Evidence Required In `tech-done.md`

The `full-stack-software-engineer` must return:

1. Actual changed files.
2. Verification command outputs for Python, workstation test/build/lint, anchor `rg`, and scoped `git diff --check`.
3. Positive local/mock create test returning `local_mock_operator_dropoff_acceptance_event_written`.
4. Idempotent update test returning `local_mock_operator_dropoff_acceptance_event_updated`.
5. UI receipt test proving the O7 panel renders `operator.dropoff_acceptance`, receipt schema, write status, and fixed false fields.
6. Fail-closed tests for unsafe base URL, task mismatch, unsupported event type, unsafe refs/content, dangerous true claims, and invalid O6 response.
7. Remaining risk and proof boundary.

## Risk Boundary

Accepted proof after successful implementation:

- selected-task operator action request construction
- O6 local archive event write/readback receipt for `operator.dropoff_acceptance`
- O7 UI receipt display
- fail-closed validation

Rejected proof:

- real operator action
- delivery success
- route execution
- HIL
- safe-to-control
- production cloud
- production DB/queue
- OSS/CDN
- 4G/SIM
- real browser/phone session
- `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- WAVE ROVER UART
- robot movement or robot control

Expected OKR result: O5 remains about `85%`, O1 remains about `94%`, O6/O7 remain about `93%`, main percentages unchanged, KR `不归档`.
