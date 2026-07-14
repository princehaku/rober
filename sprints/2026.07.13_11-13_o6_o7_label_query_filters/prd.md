# PRD - O6/O7 Label Query Filters

## Product Summary

O6 local/mock archive labels must be queryable by `robot_id`, `task_id`, and `date` on `GET /api/o6/archive/labels`. The feature should make label review and training-data preparation more usable without pretending that the system is connected to production cloud or real robot data.

Proof boundary: `software_proof_o6_o7_label_query_filters_only`.

## User Value and Product North Star

Operators need to review labels for a specific robot, a specific task, or a specific day. Without these filters, `/api/o6/archive/labels` can only act as a broad list endpoint, which makes O6 KR2 and O7 labeling workflows harder to verify.

The north star remains a fixed-route trash delivery product whose task evidence can be reviewed by non-ROS users. This PRD improves the evidence lookup contract; it does not move the robot or complete the delivery loop.

## Goals

- Add safe optional `robot_id`, `task_id`, and `date` filters to `GET /api/o6/archive/labels`.
- Keep existing `status` and `limit` behavior backward compatible.
- Make all filters AND together when multiple query parameters are present.
- Return an explicit applied filter summary so O7 and tests can verify the query contract.
- Fail closed on malformed or unsafe query values.
- Sync O6 interface docs and, if needed, O7 consumer docs/tests.

## Non Goals

- No production cloud integration.
- No real robot archive ingestion.
- No real annotation API or dataset export.
- No route execution, delivery, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, controller/BT, WAVE ROVER UART, or production external evidence.
- No OKR percentage increase or KR archive during the plan phase.

## Required Query Semantics

Endpoint:

```text
GET /api/o6/archive/labels?robot_id=<robot_id>&task_id=<task_id>&date=<YYYY-MM-DD>&status=<status>&limit=<n>
```

Filter rules:

- `robot_id`: exact match against the task/label robot identity already stored by O6.
- `task_id`: exact match against the task id already stored by O6.
- `date`: exact UTC calendar date in `YYYY-MM-DD` format. Implementation must use the label timestamp if present; if the current label schema has no label timestamp, it may use task time as a documented local/mock fallback and must expose that as the filter source in the response/docs.
- `status`: preserve existing status filter semantics.
- `limit`: preserve existing limit semantics and safe maximum clamping.
- Multiple filters compose as logical AND.
- Safe but unknown `robot_id`, `task_id`, or `date` returns a valid empty result, not leaked unrelated labels.
- Malformed or unsafe query values return a fail-closed error response and must not mutate the archive store.

## Response Contract

The label list response should continue using the existing O6 labeling schema, with additive filter metadata:

- `schema=trashbot.o6.archive_labeling.v1`
- `source=local_mock_labeling`
- `proof_status=not_proven`
- `label_query_filters_ready_not_production_proof=true`
- `applied_filters.robot_id`
- `applied_filters.task_id`
- `applied_filters.date`
- `applied_filters.status`
- `applied_filters.limit`
- `filter_semantics=and`
- `filtered_result_count`
- fixed false fields preserved:
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

Unsafe query responses should use a stable blocked reason such as `invalid_label_query_filter` and must not echo raw unsafe values beyond a short safe field name.

## Acceptance Criteria

1. A seeded local/mock archive with at least two robots, two tasks, two dates, and two statuses returns only matching summaries for `robot_id`.
2. The same fixture returns only matching summaries for `task_id`.
3. The same fixture returns only matching summaries for `date`.
4. `robot_id + task_id + date + status + limit` compose as AND and return deterministic counts.
5. Safe unknown filter values return a valid empty list with `filtered_result_count=0`.
6. Invalid date, unsafe path-like text, credential-like URL text, token-like text, overlong ids, and malformed limit fail closed with no store mutation and no unrelated labels.
7. O6 interface documentation describes the new filters and the proof boundary.
8. If O7 adapter/tests consume the label list, they verify the filtered result and keep all control/action flags disabled.

## OKR Mapping

- O6 KR2: directly targeted. This hardens querying task records and labeling results by `robot_id`, `task_id`, and `date`.
- O7 KR4: secondary support. O7 labeling UI/adapter may consume the contract, but only as observe-only software proof.
- O5: not targeted because external production evidence is unavailable.
- O1/O3: not targeted because the next useful live step requires explicit operator approval and current live HIL evidence.

Direction judgment: continue O6/O7 for this local/mock query gap while O5 and current live HIL remain blocked. Do not replace OKR direction, do not archive KR, and do not claim production readiness.

## Risks

- Date semantics can drift if label timestamps are missing. The implementation must document whether it uses label time or task time fallback.
- Query filters can accidentally leak labels from another robot or task. Tests must include cross-robot and cross-task fixtures.
- A broad read endpoint can tempt overclaiming. The response and docs must keep `software_proof_o6_o7_label_query_filters_only` and fixed false fields visible.
- O7 coupling can expand scope. O7 changes should be limited to tests/adapter semantics if needed.

## Sprint Documents

Current planning documents:

- `sprints/2026.07.13_11-13_o6_o7_label_query_filters/pre_start.md`
- `sprints/2026.07.13_11-13_o6_o7_label_query_filters/prd.md`
- `sprints/2026.07.13_11-13_o6_o7_label_query_filters/tech-plan.md`

Future documents after implementation:

- `tech-done.md` with changed files, verification logs, failure analysis, and remaining risk
- `side2side_check.md` and `final.md` after Product acceptance
