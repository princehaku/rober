# O6 Cloud Archive API Side2Side Check

## 验收对照

| 需求 / 边界 | 本轮结果 | 证据 |
| --- | --- | --- |
| `POST /api/o6/archive/tasks` 可写入最小任务 | 通过 | `test_o6_cloud_archive_tasks_endpoint_upserts_lists_and_gets_item` |
| `GET /api/o6/archive/tasks` 可列出任务 | 通过 | 同一单测覆盖写入后列表读取 |
| `GET /api/o6/archive/tasks/<task_id>` 可读取详情 | 通过 | 同一单测覆盖详情读取 |
| duplicate `task_id` idempotent upsert | 通过 | 同一单测覆盖 second POST 返回 `write_status=updated` / `duplicate=true` |
| 状态文件由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 注入 | 通过 | unittest `setUp()` 使用临时 `o6_archive_state.json`，并断言文件存在 |
| 坏 JSON fail closed | 通过 | `test_o6_cloud_archive_tasks_endpoint_rejects_bad_json_missing_fields_and_time_order` |
| 缺字段 fail closed | 通过 | 同一单测覆盖缺 `events` |
| 倒序时间 fail closed | 通过 | 同一单测覆盖 `finished_at_ms < started_at_ms` |
| 数组过大 fail closed | 通过 | `test_o6_cloud_archive_tasks_endpoint_rejects_unsafe_or_oversized_payloads` |
| unsafe content fail closed | 通过 | 同一单测覆盖 `Authorization: Bearer leaked-token` |
| missing detail fail closed | 通过 | `test_o6_cloud_archive_tasks_endpoint_missing_detail_fails_closed` |
| 响应固定 not-proven 边界 | 通过 | GET 空列表和 upsert/detail 响应固定 false 字段 |
| 文档同步 | 通过 | `cloud-relay/README.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md` 已更新 |

## CEO / Product 边界对照

- CEO 要求“设计好才能开始写功能点”：本轮 `pre_start.md`、`prd.md`、`tech-plan.md` 已先完成，再进入实现。
- O6 0% 最低 Objective：本 sprint 直接覆盖 O6-KR2 / KR3 / KR6 的 local/mock MVP 数据源形状。
- 不证明真实云：响应和文档均明确 `real_cloud_db_connected=false`、`real_oss_connected=false`、`connects_cloud_production=false`。
- 不控制机器人：响应固定 `robot_control_executed=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 不触碰旧 sprint：`sprints/2026.06.09_00-01_o6-local-cloud-archive-mvp/` 未修改或删除。

## 验收结论

本轮 O6 MVP local/mock file-backed archive API 达到 `tech-plan.md` 的工程验收口径，可以作为 O7 route replay / labeling / voice / safe command 后续开发的 O6-shaped 数据源。验收边界仍是 software proof，不能上升为真实 O6 production backend proof。
