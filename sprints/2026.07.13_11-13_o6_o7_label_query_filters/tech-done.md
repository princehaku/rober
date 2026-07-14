# Tech Done - O6/O7 Label Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`
- Implementation owner: `full-stack-software-engineer`
- Completion time: 2026-07-13 11:31 CST
- Proof boundary: `software_proof_o6_o7_label_query_filters_only`
- OKR boundary: support-only local/mock query hardening; no OKR main percentage change and no KR archive.

## Actual Changes

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - Added fail-closed label-list query parsing for `robot_id`, `task_id`, `date`, existing `status`, and `limit`.
  - Added safe bounded identifier validation, strict `YYYY-MM-DD` UTC date validation, duplicate query rejection, path/URL/token/raw/base64-like rejection, and unknown query-key rejection.
  - Applied filters as logical AND before applying `limit`.
  - Added additive response metadata: `label_query_filters_ready_not_production_proof=true`, `applied_filters`, `filter_semantics=and`, `filtered_result_count`, and optional `date_filter_source`.
  - Date filtering prioritizes label timestamps (`updated_at_ms`, then `created_at_ms`, then compatible label timestamp fields) and falls back to task `finished_at_ms` / `started_at_ms` only when label timestamps are absent.
  - Preserved fixed false fields: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `submit_enabled=false`, `rollback_enabled=false`, `dataset_export_available=false`, `real_annotation_api_connected=false`, `real_dataset_export_connected=false`, `connects_cloud_production=false`, `robot_control_executed=false`.
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - Added multi-robot, multi-task, multi-date, multi-status list-filter tests.
  - Added AND composition and post-filter `limit` tests.
  - Added safe unknown filter empty-result test.
  - Added invalid date, path-like, credential URL, raw/base64-like, overlong id, and duplicate query fail-closed tests.
  - Verified invalid queries do not mutate the label store.
- `docs/interfaces/o6_cloud_archive_api.md`
  - Documented `GET /api/o6/archive/labels` filter parameters, AND semantics, date source priority/fallback, fail-closed behavior, fixed false fields, and `software_proof_o6_o7_label_query_filters_only`.

## O7 Touch Decision

- O7 code was not touched.
- Reason: `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` only uses `/api/o6/archive/labels` for submit and task export paths, and consumer detail reads labels through task detail/consumer endpoints. It does not call or expose the label-list filter semantics added here.
- `docs/product/pc_tools_workstation.md`, `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`, and `pc-tools/workstation/test/App.test.ts` were already dirty in the worktree before this run; this implementation did not edit them.
- Because no O7 file was edited by this run, workstation `npm run test && npm run build && npm run lint` was not required by the acceptance plan.

## Verification

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

- Result: passed, exit 0.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

- Result: passed.
- Key output: `Ran 187 tests in 83.049s` / `OK`.

```bash
rg -n "label query filters|/api/o6/archive/labels|robot_id|task_id|date|label_query_filters_ready_not_production_proof|software_proof_o6_o7_label_query_filters_only|safe_to_control=false|delivery_success=false|connects_cloud_production=false" \
  docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md onboard/src/ros2_trashbot_behavior pc-tools/workstation
```

- Result: passed, exit 0.
- Note: output is very large and was truncated by the runner, but the new O6 doc/relay/test anchors were present.

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

- Result: passed, exit 0.

## Failure Positioning and Fixes

- No verification failure remained.
- During self-check, the first list-payload edit briefly needed a local return-shape correction so `date_filter_source` could be appended to a `payload` object. This was fixed before `py_compile` and unit tests.

## Remaining Risks

- This remains local/mock file-backed O6 behavior only.
- It does not prove production cloud, production DB/queue, TLS/4G, OSS/CDN, real annotation API, real dataset export, real robot data, route execution, delivery, operator acceptance, HIL, or safe-to-control.
- Query capacity and index performance are not production-proven; the current implementation filters in local memory from the file-backed mock store.
- Worktree contains pre-existing dirty changes outside this sprint and even inside some touched files; this run did not revert or clean them.
