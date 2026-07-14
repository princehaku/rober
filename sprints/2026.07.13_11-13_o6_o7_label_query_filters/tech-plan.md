# Tech Plan - O6/O7 Label Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `full-stack-software-engineer`
- Supporting owner: `full-stack-software-engineer` for optional O7 adapter/tests
- Plan status: planning_only
- Proof boundary: `software_proof_o6_o7_label_query_filters_only`

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is O5 at about `85%`.
2. This sprint does not target O5.
3. Reason for pivot: O5 still lacks real public HTTPS/TLS, real 4G/SIM, production DB/queue, production worker cutover, OSS/CDN live traffic, and real phone/browser evidence. The current environment cannot create that external production evidence. Recent O1/O3 runs also consumed current stop path readiness and mock-only stop HIL capture gate; their next meaningful step requires explicit operator approval plus current live HIL evidence. Repeating helper/export/readiness/route-intent, packet packaging, bounded-plan packaging, stop-path readiness, mock-only stop HIL capture gate, or O6/O7 readback-only wrapper is explicitly disallowed by automation memory.
4. This sprint targets the next movable software gap: `/api/o6/archive/labels` currently has a known label query filter gap, while O6 KR2 requires querying task records and annotation results by `robot_id`, `task_id`, and `date`.
5. OKR credit boundary: implementation may harden O6/O7 local/mock query semantics, but it remains `software_proof_o6_o7_label_query_filters_only` unless later evidence includes real production cloud, real robot data, route execution, delivery, operator acceptance, or HIL.

## Current Technical Facts

- O6 docs already define `POST /api/o6/archive/labels`, `GET /api/o6/archive/labels`, `GET /api/o6/archive/labels/<task_id>`, and `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`.
- Prior triage found the list endpoint gap: `GET /api/o6/archive/labels` handled only `status` and `limit`, not `robot_id`, `task_id`, or `date`.
- O7 has an existing labeling path through O6 archive labels and consumer read adapters, but the primary goal is O6 query correctness. O7 work should be minimal and only verify consumer semantics if needed.
- All O6/O7 labeling responses must remain local/mock, fail-closed, and fixed false for control, delivery, production cloud, and robot execution fields.

## Planned File Scope for Implementation

Full-stack implementation may touch:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md` only if O7 consumer behavior or user-facing PC docs need to mention the filter contract
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` only if O7 currently exposes label-list semantics through the adapter
- `pc-tools/workstation/test/App.test.ts` or nearby O7 tests only if the O7 adapter is touched

This planning run must not modify those implementation files. Future implementation must keep changes inside the owner scope and document actual touched files in `tech-done.md`.

## Implementation Plan

### 1. O6 Query Parser

Add a small parser for optional `robot_id`, `task_id`, and `date` query parameters on `GET /api/o6/archive/labels`.

Rules:

- Accept only bounded, safe identifier strings for `robot_id` and `task_id`.
- Accept only `YYYY-MM-DD` for `date`.
- Reject slash/path-like text, credential URLs, token-like values, raw/base64-like blobs, empty strings, and overlong strings.
- Preserve existing `status` and `limit` behavior.
- On invalid query values, return a stable fail-closed response with `invalid_label_query_filter` and do not mutate the store.

### 2. O6 Store/List Filtering

Apply filters to label summaries as logical AND:

- `robot_id` must match the task/label robot identity.
- `task_id` must match exact task identity.
- `date` must match UTC date from label timestamp if available; otherwise use a documented task-time fallback and expose `date_filter_source`.
- `status` keeps existing behavior.
- `limit` is applied after filtering and remains safely bounded.

Safe unknown filter values should return an empty list with `filtered_result_count=0`.

### 3. Response Metadata

Add additive metadata without breaking existing consumers:

- `label_query_filters_ready_not_production_proof=true`
- `applied_filters`
- `filter_semantics=and`
- `filtered_result_count`
- optional `date_filter_source`
- fixed false fields:
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `submit_enabled=false`
  - `rollback_enabled=false`
  - `dataset_export_available=false`
  - `real_annotation_api_connected=false`
  - `real_dataset_export_connected=false`
  - `connects_cloud_production=false`
  - `robot_control_executed=false`

Do not echo unsafe raw query values, absolute paths, credential URLs, tokens, tracebacks, raw payloads, or unrelated labels.

### 4. O7 Minimal Compatibility

Inspect whether O7 consumer read or annotation adapter paths call `GET /api/o6/archive/labels` list semantics.

- If yes, add a minimal adapter/test update that passes through or verifies filtered O6 results.
- If no, document that no O7 code change is needed and keep O7 untouched.
- In either case, O7 must remain observe-only and must not expose submit/export/control as enabled.

### 5. Documentation Sync

Update O6 interface docs to describe:

- New query params: `robot_id`, `task_id`, `date`
- Date semantics and fallback source if applicable
- AND composition with `status` and `limit`
- Fail-closed invalid query behavior
- `software_proof_o6_o7_label_query_filters_only`
- Non-production and non-HIL boundaries

Update O7/PC docs only if O7 behavior or tests are changed.

## Interface Impact

Backward compatible additions:

- Existing `GET /api/o6/archive/labels?status=...&limit=...` keeps working.
- New query params are optional.
- Unknown safe filter values return empty results, not an error.
- Invalid unsafe values return fail-closed error.

No changes:

- `POST /api/o6/archive/labels`
- `GET /api/o6/archive/labels/<task_id>`
- `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`
- Production cloud, real annotation API, real dataset export, robot control, route execution, delivery, or HIL interfaces

## Acceptance Commands for Implementation

Full-stack owner must run and record at least:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

If O7 files are touched:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

Always run:

```bash
rg -n "label query filters|/api/o6/archive/labels|robot_id|task_id|date|label_query_filters_ready_not_production_proof|software_proof_o6_o7_label_query_filters_only|safe_to_control=false|delivery_success=false|connects_cloud_production=false" \
  docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md onboard/src/ros2_trashbot_behavior pc-tools/workstation
```

```bash
git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/interfaces/o6_cloud_archive_api.md \
  docs/product/pc_tools_workstation.md \
  pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts \
  pc-tools/workstation/test/App.test.ts \
  sprints/2026.07.13_11-13_o6_o7_label_query_filters
```

## Product Plan Validation Commands

This plan-only run must run and record:

```bash
rg -n "sprint_type: epic|O5|O6|O7|label query filters|/api/o6/archive/labels|robot_id|task_id|date|OKR 最低优先级核对|software_proof_o6_o7_label_query_filters_only" sprints/2026.07.13_11-13_o6_o7_label_query_filters
```

```bash
git diff --check -- sprints/2026.07.13_11-13_o6_o7_label_query_filters
```

## Acceptance Criteria

- Query filters `robot_id`, `task_id`, and `date` exist on list labels API.
- Filters compose with `status` and `limit` as logical AND.
- Cross-robot and cross-task fixtures prove no unrelated labels leak.
- Safe unknown filters return an empty response.
- Invalid date and unsafe query values fail closed without store mutation.
- Response metadata exposes `applied_filters`, `filter_semantics`, and `filtered_result_count`.
- All fixed false fields remain false.
- O6 docs are updated.
- O7 is either untouched with a documented reason or minimally tested for filtered semantics.
- `tech-done.md` later records actual files, verification output, failure定位 if any, and remaining risk.

## Risks and Mitigations

- Date ambiguity: require implementation to document label timestamp vs task-time fallback and expose `date_filter_source`.
- Scope creep into O7 UI: O7 work is optional and only for adapter/test semantics.
- Overclaiming: every response and doc must retain `software_proof_o6_o7_label_query_filters_only` and not-proven/fixed-false fields.
- Query leakage: tests must seed multiple robots/tasks/dates/statuses and assert exact filtered counts.
- Dirty worktree risk: implementation must not revert or clean unrelated changes in `OKR.md`, progress log, or other sprint directories.

## Sub Agent Dispatch Draft

Use one `full-stack-software-engineer` worker for implementation because the file scope is concentrated and O7 is optional/minimal.

Required output from the worker:

1. Actual changed files.
2. Verification command logs.
3. Failure定位 and fixes if any.
4. Remaining risk.
5. `tech-done.md` update for this sprint.
