# Tech Plan - O6 Archive Task Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o6_archive_task_query_filters_only`

## Technical Plan

1. Add a small archive task query validator near existing O6 archive query helpers.
2. Extend `FileBackedO6CloudArchiveStore.list_tasks()` to accept a filter object and apply filters before building the existing list response.
3. Wire `GET /api/o6/archive/tasks` to parse `parse_qs(parsed.query)`, validate query values, and call the filtered `list_tasks()`.
4. Add response metadata without changing existing task item summaries:
   - `archive_task_query_filters_ready_not_production_proof`
   - `applied_filters`
   - `filter_semantics`
   - `filtered_result_count`
   - optional `date_filter_source`
5. Add unit tests under `test_remote_cloud_relay.py` covering:
   - multi-robot / multi-task filtering
   - date filtering with started timestamp and finished fallback
   - status filtering
   - AND semantics and post-filter limit
   - safe nonexistent ids return empty result
   - invalid date, duplicate query, unknown query key, path/URL/raw/base64-like values fail closed
   - failed GET does not mutate archive state
6. Update `docs/interfaces/o6_cloud_archive_api.md` with the query contract and rejected claims.
7. Worker writes `tech-done.md` with actual changes, verification, failures/fixes, remaining risk.

## File Scope

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.13_12-13_o6_archive_task_query_filters/tech-done.md`

Do not edit other files. Do not revert existing dirty changes.

## Interface Impact

- Additive query semantics for `GET /api/o6/archive/tasks`.
- Existing no-query response should remain compatible and continue to return local/mock task list.
- Failure code for bad query should be `400` with safe phone error reason `invalid_archive_task_query_filter` or equivalent safe reason.

## Validation Commands

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

```bash
rg -n "archive task query filters|archive_task_query_filters_ready_not_production_proof|software_proof_o6_archive_task_query_filters_only|invalid_archive_task_query_filter|filter_semantics=and|safe_to_control=false|delivery_success=false|connects_cloud_production=false" docs/interfaces/o6_cloud_archive_api.md onboard/src/ros2_trashbot_behavior
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.13_12-13_o6_archive_task_query_filters
```

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 `85%`。
- 本 sprint 是否针对该 Objective：否，主攻 Objective 6。
- 如不针对，理由：O5 当前需要真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser 材料；当前环境没有新增真实外部材料。最近 O1/O3 current live HIL/operator approval blocker 也已连续被 stop-path readiness 和 mock-only stop HIL capture gate 消费，本轮选择不依赖真实外部条件、且未重复上一轮 label filters 的 O6 archive task query contract gap。
- final.md 收口时需复核：O5 blocker 是否仍成立；如果期间出现真实 production/cloud 或 operator-approved live HIL 材料，下一轮必须优先切回该材料。

## Risk Boundary

This sprint must remain `software_proof_o6_archive_task_query_filters_only`. It must not claim production cloud, production DB/queue, production query capacity, real robot data, route execution, delivery, operator acceptance, HIL, safe-to-control, or O5 external evidence.
