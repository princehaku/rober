# Side2Side Check - O6/O7 Label Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Acceptance time: 2026-07-13 11:13 CST
- Acceptance status: accepted
- Proof boundary: `software_proof_o6_o7_label_query_filters_only`

## User Value and Product North Star

North star remains unchanged: ordinary users should be able to hand trash to the robot and later have the task evidence searchable, reviewable, and improvable without knowing ROS2 or shell workflows.

This sprint improves the evidence lookup layer only. O6 local/mock label summaries can now be queried by `robot_id`, `task_id`, `date`, `status`, and `limit`, so label review no longer depends on scanning a broad list. This supports O6 KR2 and the O7 labeling workflow, but it remains software proof.

## OKR Mapping and Direction Judgment

- O5: continue blocked at about `85%`. This sprint did not produce production cloud, public HTTPS/TLS, real 4G/SIM, production DB/queue, worker cutover, OSS/CDN live traffic, real phone, or real browser evidence.
- O6: continue at about `93%`. Accepted delta is local/mock label query filters contract hardening only.
- O7: continue observe-only at about `93%`. O7 was not touched because the current O7 adapter does not consume label-list filter semantics.
- O1/O3: pause for this run. The next useful lane still requires explicit operator approval and current live HIL/current live route evidence.
- Direction judgment: continue O6/O7 software gap while O5 and current live HIL are blocked. 主百分比不调整 and KR 不归档.

## Side2Side Acceptance Check

| Requirement | Product Result | Evidence |
| --- | --- | --- |
| `GET /api/o6/archive/labels` supports `robot_id` | accepted | `tech-done.md` records fail-closed query parsing and multi-robot tests |
| `GET /api/o6/archive/labels` supports `task_id` | accepted | `tech-done.md` records exact task filter tests |
| `GET /api/o6/archive/labels` supports `date` | accepted | O6 docs define UTC `YYYY-MM-DD` and `date_filter_source` |
| Filters compose with `status` and `limit` | accepted | `filter_semantics=and`; `limit` is applied after filtering |
| Response exposes metadata | accepted | `label_query_filters_ready_not_production_proof=true`, `applied_filters`, `filtered_result_count`, `date_filter_source` |
| Unsafe values fail closed | accepted | invalid date/path/credential/raw/base64-like/duplicate queries use `invalid_label_query_filter` |
| O6 docs synced | accepted | `docs/interfaces/o6_cloud_archive_api.md` has the label query filters section |
| O7 scope held | accepted | O7 code not touched; workstation npm checks not required |

## Verification Evidence

Full-stack worker recorded:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Result: passed.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Result: `Ran 187 tests in 83.049s OK`.

```bash
rg -n "label query filters|/api/o6/archive/labels|robot_id|task_id|date|label_query_filters_ready_not_production_proof|software_proof_o6_o7_label_query_filters_only|safe_to_control=false|delivery_success=false|connects_cloud_production=false" \
  docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md onboard/src/ros2_trashbot_behavior pc-tools/workstation
```

Result: passed, anchors present.

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

Result: passed.

## Rejected Claims

This Product acceptance does not prove production cloud, real robot data, real annotation API/export, route execution, delivery, operator acceptance, HIL, safe-to-control, O5 external evidence, or real phone/browser operation.

## Responsibility and Next Step

Responsible engineer for this increment: `full-stack-software-engineer`.

Next priority should be explicit operator-approved current live HIL or real production/cloud evidence. If those are still unavailable, choose another non-repeating software contract gap rather than repeating readback-only wrappers.

## KR Archive Judgment

No KR is archived. The work is accepted as O6/O7 local/mock label query filters contract hardening only.
