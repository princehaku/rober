# Final - O6/O7 Label Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Closeout time: 2026-07-13 11:13 CST
- Final status: accepted
- Proof boundary: `software_proof_o6_o7_label_query_filters_only`

## Product Acceptance Summary

Product accepts this sprint as O6/O7 local/mock label query filters contract hardening only.

Accepted facts:

- `GET /api/o6/archive/labels` now supports `robot_id`, `task_id`, and `date` filters.
- New filters compose with existing `status` and `limit` as AND.
- `limit` is applied after filtering.
- Response metadata includes `label_query_filters_ready_not_production_proof=true`, `applied_filters`, `filter_semantics=and`, `filtered_result_count`, and `date_filter_source`.
- Invalid/unsafe query values fail closed with `invalid_label_query_filter`.
- O6 docs were updated.
- O7 was not touched because the O7 adapter does not consume label-list filter semantics.

## User Value and North Star

This makes local/mock label evidence searchable by robot, task, and day. It helps operators and future O7 label review flows find the right evidence without broad manual scanning.

The product north star remains a fixed-route trash delivery robot with reviewable task evidence for non-ROS users. This sprint improves reviewability, not robot movement or production operation.

## OKR Result

- O5 remains about `85%`: blocked on production cloud/external evidence.
- O6 remains about `93%`: accepted software contract hardening only.
- O7 remains about `93%`: no O7 code delta in this sprint.
- O1 remains about `94%`: next useful progress requires explicit operator/current live HIL or live route evidence.
- 主百分比不调整.
- KR 不归档.

Direction judgment: continue O6/O7 only as a movable software contract gap while O5 and current live HIL remain blocked. Next sprint should prefer explicit operator-approved current live HIL or real production/cloud evidence; if still unavailable, choose a non-repeating software contract gap.

## Verification

Worker verification recorded in `tech-done.md`:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Passed.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Passed: `Ran 187 tests in 83.049s OK`.

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

Passed.

Product closeout verification is captured in `artifacts/product_acceptance_label_query_filters.json`.

## Rejected Claims and Risk

This sprint does not prove production cloud, real robot data, real annotation API/export, route execution, delivery, operator acceptance, HIL, safe-to-control, O5 external evidence, or real phone/browser behavior.

Remaining risk:

- Filtering is local/mock and file-backed, not production query capacity proof.
- O7 behavior was not retested because no O7 files were changed.
- The next meaningful progress still depends on current live HIL/operator approval or real production/cloud evidence.

## Historical KR Judgment

No KR moves to history. Keep this sprint as support-only O6/O7 contract evidence under the current OKR, with proof boundary `software_proof_o6_o7_label_query_filters_only`.
