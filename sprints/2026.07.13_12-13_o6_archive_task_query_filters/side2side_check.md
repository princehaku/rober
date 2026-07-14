# Side2Side Check - O6 Archive Task Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`
- Product acceptance time: 2026-07-13 12:29 CST
- Product status: accepted as O6 local/mock archive task query filters only
- Proof boundary: `software_proof_o6_archive_task_query_filters_only`

## 对照验收

- 计划要求 `GET /api/o6/archive/tasks` 支持 `robot_id`、`task_id`、`date=YYYY-MM-DD`、`status`、`limit` 查询；实际实现已覆盖。
- 计划要求 filters 使用 AND 语义且 `limit` 在过滤后应用；`tech-done.md` 记录的单元测试已覆盖组合过滤与 post-filter limit。
- 计划要求 invalid/unsafe query fail-closed；实际覆盖 unknown key、重复 query、非法日期、过长 id、path-like、URL-like、credential/token、raw/base64-like 值，并返回 `invalid_archive_task_query_filter`。
- 计划要求响应 metadata 暴露 local/mock proof 边界；实际包含 `archive_task_query_filters_ready_not_production_proof=true`、`archive_task_query_filters_proof_scope=software_proof_o6_archive_task_query_filters_only`、`applied_filters`、`filter_semantics=and`、`filtered_result_count` 和可选 `date_filter_source`。

## 验证证据

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：通过，`Ran 189 tests in 83.926s OK`。
- required anchor `rg`：通过，命中 implementation、tests、interface docs 和 sprint docs。
- scoped `git diff --check`：通过，无 whitespace error。

## 拒绝声明

本轮不接受为 production cloud、production DB/queue、真实机器人数据、production query capacity、真实手机/browser、route execution、delivery、operator acceptance、HIL、safe-to-control 或 O5 external evidence。
