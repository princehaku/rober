# O6 Cloud Archive API

## Scope

`POST /api/o6/archive/tasks`
`GET /api/o6/archive/tasks`
`GET /api/o6/archive/tasks/<task_id>`
`POST /api/o6/archive/labels`
`GET /api/o6/archive/labels`
`GET /api/o6/archive/labels/<task_id>`

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

## Response Contract（Archive tasks）

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

## O6 标注本地 mock contract

`POST /api/o6/archive/labels` 及其查询接口是 O6 标注回路的 local/mock 入口，仍不连接真实生产云、OSS 或训练服务，不会下发控制。

### Request Contract（POST）

- `robot_id`
- `task_id`
- `labels`：数组，长度限制 `<= O6_CLOUD_LABELING_MAX_LABELS`（当前 64）

`labels[]` 中每条必须包含：

- `item_id`
- `item_type`
- `label_type`
- `value`

可选字段：

- `confidence`
- `annotator_id`
- `evidence_ref`
- `notes`

### Request constraints

- `task_id` 必须已经存在于 local O6 archive store 中。
- `robot_id` 必须与目标 task 的 `robot_id` 完全一致。
- `labels` 必须为数组，且不得空。
- 任何字段长度仍按 O6 local/mock 标注常量上限限制：
  - `item_id <= 80`
  - `item_type <= 120`
  - `label_type <= 120`
  - `value <= 240`
  - `annotator_id / evidence_ref / notes <= 512`

### Response Contract（POST/List/Detail）

固定成功字段：

- `schema=trashbot.o6.archive_labeling.v1`
- `schema_version=1`
- `source=local_mock_labeling`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `submit_enabled=false`
- `rollback_enabled=false`
- `dataset_export_available=false`
- `real_annotation_api_connected=false`
- `real_dataset_export_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `not_proven` 至少包含
  - `real_annotation_submit_success`
  - `real_annotation_review_api`
  - `real_dataset_export`
  - `real_o7_labeling_production`

成功响应还带：

- `write_status`：`created | updated`
- `duplicate`：首次写入 `false`，存在至少一个幂等键时 `true`
- `label_summary`
- `itemized_labels[]`（detail 接口）
- `task_summary[]`（list 接口）

重复语义（幂等）：`task_id + item_id + label_type` 为幂等键。

- 首次提交该 task 的 label 组合 → `201` + `write_status=created` + `duplicate=false`
- 重复提交命中幂等键 → `200` + `write_status=updated` + `duplicate=true`

### Labeling List Contract（GET /api/o6/archive/labels）

`task_summary` 仅返回任务级摘要，不原样回显完整 `labels`。支持：

- `status=pending|labeled|all`（默认 `all`）
- `limit`（正整数，默认 50，上限 100）

响应字段包含：

- `status`：`local_mock_labeling_ready | blocked_not_proven`
- `status_filter`
- `limit`
- `task_summary[]`（`task_id/robot_id/task_status/pending_item_count/labeled_item_count/latest_label_updated_at_ms/itemized_label_count/selected`）
- `label_summary.task_count`
- `label_summary.pending_task_count`
- `label_summary.partial_task_count`
- `label_summary.labeled_task_count`
- `blocked_reasons`

### Labeling Detail Contract（GET /api/o6/archive/labels/<task_id>）

- `task_id/robot_id`
- `task_status`
- `itemized_labels[]`
- `label_summary`

`task_status` 的状态来源于 `labels` 完整度（`pending | partial | labeled | blocked`）。

### Fail-Closed / 安全告警

- `/api/o6/archive/labels` 及详情接口在以下场景返回 fail-closed：
  - 坏 JSON / 非对象 JSON
  - `labels` 非数组
  - 超大数组
  - 字段类型错 / 长度越界
  - `unknown_task`
  - `unauthorized_task`
  - 不安全内容（`Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / baudrate / traceback / credentials URL）
- 失败响应不回显危险内容，不创建/更新不存在的 task。

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
