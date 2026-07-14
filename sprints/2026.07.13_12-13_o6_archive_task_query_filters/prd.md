# PRD - O6 Archive Task Query Filters

## Product Context

O6 的目标是把任务记录、事件、证据和标注沉淀为可查询的云端核心后端。当前 local/mock archive 已能存 task、events、evidence、labels、inference 和 consumer detail，但 lower-level archive task list 缺少查询过滤语义，operator 或后续 O7 接入方需要自己扫全量 task 后再筛选。

## User Value

运营或调试人员需要快速定位某台机器人、某个任务、某一天或某个状态的 archive task。这个能力应先在 local/mock file-backed archive 中用稳定合同证明，再等待真实生产 DB/queue 与云端查询容量材料。

## Requirements

1. `GET /api/o6/archive/tasks` supports optional query filters:
   - `robot_id`
   - `task_id`
   - `date=YYYY-MM-DD`
   - `status`
   - `limit`
2. Filters compose as AND.
3. `limit` applies after filtering and uses existing safe limit bounds.
4. `date` uses task timestamps in UTC:
   - Prefer `started_at_ms`.
   - Fall back to `finished_at_ms` only when `started_at_ms` is missing.
5. Safe but nonexistent `robot_id` / `task_id` returns an empty task list, not another task.
6. Unsafe, duplicated, unknown, overlong, path-like, URL-like, credential-bearing, raw/base64-like query values fail closed with `400 invalid_archive_task_query_filter`.
7. Response metadata includes:
   - `archive_task_query_filters_ready_not_production_proof=true`
   - `applied_filters`
   - `filter_semantics=and`
   - `filtered_result_count`
   - `date_filter_source` only when `date` is requested
8. Existing response shape and fixed false fields remain compatible.

## Non Goals

- No production DB/queue proof.
- No production query index/capacity proof.
- No true phone/browser proof.
- No route execution, delivery, operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, or WAVE ROVER UART.
- No O7 UI change unless the worker discovers a direct compile/test requirement in touched files.

## Acceptance

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
- Anchor search for the new proof boundary and metadata fields.
- Scoped `git diff --check`.
