# O6 Cloud Archive API

## Scope

`POST /api/o6/archive/tasks`
`GET /api/o6/archive/tasks`
`GET /api/o6/archive/tasks/<task_id>`

这是 `remote_cloud_relay.py` 内置的本地 mock archive API。它提供 `trashbot.o6.cloud_archive.v1` 的 O6-shaped 数据源，让后续 O7 route replay / labeling / voice / safe command 可以从统一的任务存档形状继续消费，但它不连接真实云数据库，不连接真实 OSS，不下发机器人控制，也不声明 production cloud ready。

## Storage

- Store 由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 注入
- 未设置时回落到系统临时目录下的默认文件
- 这是 file-backed 本地开发/测试存储，不是生产 DB

## Request Contract

`POST /api/o6/archive/tasks` 接受小型 JSON object，必须包含：

- `robot_id`
- `task_id`
- `started_at_ms`
- `finished_at_ms`
- `trajectory_frames[]`
- `events[]`

可选字段：

- `evidence_refs[]`

`trajectory_frames[]` 和 `events[]` 都只允许小数组。当前实现上限分别是 64 和 64；`evidence_refs[]` 上限是 32。超过上限直接 fail closed。

## Response Contract

固定顶层字段：

- `schema=trashbot.o6.cloud_archive.v1`
- `source=local_mock_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

任务详情只暴露白名单字段：

- `task_id`
- `robot_id`
- `started_at_ms`
- `finished_at_ms`
- `trajectory_frames[]`
- `events[]`
- `evidence_refs[]`
- `created_at_ms`
- `updated_at_ms`
- `selected`

列表响应还包含：

- `task_list.total_tasks`
- `task_list.tasks[]`
- `selected_task`
- `latest_task`
- `summary`

## Duplicate Semantics

同一 `task_id` 采用 idempotent upsert，不返回 `409 conflict`。再次 `POST` 同一 `task_id` 会覆盖该任务的安全摘要并返回：

- 新建：`201`
- 更新：`200`
- `write_status=created | updated`
- `duplicate=true | false`

## Fail-Closed Rules

以下情况必须 fail closed：

- 坏 JSON
- 缺少 `robot_id` / `task_id` / `started_at_ms` / `finished_at_ms` / `trajectory_frames[]` / `events[]`
- `trajectory_frames[]` / `events[]` / `evidence_refs[]` 不是数组
- `finished_at_ms < started_at_ms`
- 数组过大
- 任意 unsafe content
- `Authorization`
- `Bearer`
- `token`
- `credentials URL`
- `/cmd_vel`
- 串口路径
- `baudrate`
- `traceback`

unsafe content 出现时，接口不会尝试“修复”原始请求，只会拒绝并返回安全错误摘要。

## O7 Consumption Note

O7 后续可以把这个 O6-shaped 数据源当作历史任务基础输入，再派生 route replay / labeling / voice / command 的只读视图；但这仍然只是本地 mock archive，不等于真实 O6 云存档、真实 DB 或真实 OSS 接通。
