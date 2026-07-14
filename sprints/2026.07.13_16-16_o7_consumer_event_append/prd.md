# PRD - O7 Consumer Event Append

## Product Problem

O7 can already read selected task detail and request a local/mock inference write, but the operator still lacks a general selected-task action for appending mission events such as route frame notes, elevator observations, failure markers, or operator notes into the O6 archive. Repeating query/readback wrappers will not advance the mission evidence chain. The next useful software increment is a bounded action-write path tied to a selected `task_id`.

## Product Goal

Enable PC/O7 to append a local/mock mission event for the currently selected task through O6 `POST /api/o6/archive/events`, and show a receipt that proves only archive event write semantics.

The user-facing goal is operational observability: after a route replay, keyframe, mock delivery result, or other local artifact is selected, the operator can record a mission event against the same task without opening raw O6 tooling.

## OKR Mapping And Direction

- Objective 6: supports the archive event KR by consuming O6 `POST /api/o6/archive/events` through a safe consumer path.
- Objective 7: supports the PC operations platform by adding a selected-task action-write control surface for mission evidence.
- Objective 5 remains the numeric lowest at about `85%`, but this sprint does not target O5 because the current blocker is external production evidence, specifically the recent `blocked_http_status_not_success_class` result.
- Direction judgment: continue O7/O6 with a bounded local/mock action-write slice; keep main percentages flat and `不归档` unless later implementation proves stronger evidence.

## Required Inputs

The action must consume the following fields:

- `task_id`: required by selected path and must match request body if body includes it.
- `robot_id`: required and must match the existing O6 archive task.
- `event_id`: required idempotency key for O6 event upsert.
- `event_type`: required and limited to O6 allowed event types.
- `occurred_at_ms`: required and must stay within the archived task time window enforced by O6.
- `evidence_ref` or `evidence_refs`: at least one safe reference must be consumed by O7 and normalized to O6 `evidence_refs`.

Optional safe fields:

- `summary`
- `severity`
- `metadata`
- `pose`, only if the existing O6 archive event validator accepts it.

## Interface Shape

Planned O7 endpoint:

```text
POST /api/o7/consumer-read/tasks/:taskId/events/append?baseUrl=<local-loopback-url>
```

Planned O7 request body:

```json
{
  "robot_id": "robot_fixture",
  "task_id": "task-consumer-001",
  "event_id": "evt-task-consumer-001-operator-note-001",
  "event_type": "operator.note",
  "occurred_at_ms": 1500,
  "summary": "local mock operator note",
  "severity": "info",
  "evidence_ref": "events/operator-note-001.json",
  "evidence_refs": ["events/operator-note-001.json"],
  "metadata": {
    "source": "pc_o7_consumer_detail",
    "local_mock": true
  }
}
```

O7 must forward to O6 as:

```text
POST /api/o6/archive/events
```

```json
{
  "robot_id": "robot_fixture",
  "task_id": "task-consumer-001",
  "events": [
    {
      "event_id": "evt-task-consumer-001-operator-note-001",
      "event_type": "operator.note",
      "occurred_at_ms": 1500,
      "summary": "local mock operator note",
      "severity": "info",
      "evidence_refs": ["events/operator-note-001.json"],
      "metadata": {
        "source": "pc_o7_consumer_detail",
        "local_mock": true
      }
    }
  ]
}
```

Planned O7 receipt schema:

```text
trashbot.pc_tools_workstation.o7_consumer_mission_event_append_result.v1
```

Receipt required fields:

- `append_status`: `local_mock_event_written`, `local_mock_event_updated`, or `fail_closed`.
- `remote_endpoint`: `/api/o6/archive/events`.
- `requested_task_id`, `task_id`, `robot_id`, `event_id`, `event_type`, `occurred_at_ms`.
- `write_status`, `duplicate`, `created_count`, `updated_count`.
- `archive_event_written`.
- `events_written_count` and `event_summary`.
- `evidence_refs_consumed`.
- Fixed false fields: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`.

## Acceptance Criteria

- O7 selected-task action appends exactly one safe local/mock mission event to O6 archive events.
- O7 normalizes `evidence_ref` and `evidence_refs` into a bounded safe `evidence_refs` array.
- O7 accepts both created and updated O6 receipts, using `event_id` as idempotency key.
- O7 fail-closes before contacting O6 for non-local base URL, task mismatch, missing required fields, unsupported event type, unsafe refs, raw payload content, arrays where scalar is required, and any dangerous true safety/production claim.
- O7 fail-closes after contacting O6 if the response schema/source/proof status or fixed false fields drift.
- UI shows the receipt without implying real delivery, real cloud, HIL, safe-to-control, or primary action readiness.

## Responsibility

Owner: `full-stack-software-engineer`.

No Hardware, Robot Algorithm, or Robot Software owner is needed unless implementation discovers that the existing O6 `archive/events` contract is missing a field required by this PRD. If that happens, the owner must stop and return a narrow blocker instead of widening scope silently.

## Product Risks

- This is local/mock proof only; it can improve the evidence authoring workflow but cannot raise O5 or prove production archive.
- If the O7 receipt accepts a dangerous true claim from either request or O6 response, the UI could overstate safety. Fixed false fields are therefore acceptance-critical.
- If `task_id` or `robot_id` mismatch is not caught, events could be attached to the wrong mission record.
- If this becomes another read-only display, it fails the sprint goal.
