# O6 Cloud Archive API

## Scope

`POST /api/o6/archive/tasks`
`GET /api/o6/archive/tasks`
`GET /api/o6/archive/tasks/<task_id>`
`POST /api/o6/archive/labels`
`GET /api/o6/archive/labels`
`GET /api/o6/archive/labels/<task_id>`
`POST /api/o6/archive/events`
`GET /api/o6/archive/events`
`POST /api/o6/archive/evidence`
`GET /api/o6/archive/evidence`
`POST /api/o6/archive/inference`

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

`trajectory_frames[]`、`events[]` 和 `evidence_refs[]` 都只允许小数组。当前实现上限分别是 64、64 和 64。超过上限直接 fail closed。

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

## O6 事件与证据引用本地 mock contract

`POST /api/o6/archive/events`、`GET /api/o6/archive/events`、`POST /api/o6/archive/evidence`、`GET /api/o6/archive/evidence` 是 O6-KR2/O6-KR3 的任务内增量存档入口。它们复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 和既有 file-backed local/mock store，只允许附着到已存在 task，不会隐式创建 task。

### POST /api/o6/archive/events

请求必须包含：

- `robot_id`
- `task_id`
- `events[]`：1 到 64 条

每条 event 必须包含：

- `event_id`：task 内幂等键，长度 1 到 128
- `event_type`：必须是白名单类型
- `occurred_at_ms`：必须落在 task `started_at_ms..finished_at_ms` 时间窗内

可选字段：

- `pose`：仅保留 `x_m / y_m / yaw_rad / floor_id`
- `summary`：最多 512 字符
- `severity=info|warning|error`
- `evidence_refs[]`：每条 event 最多 8 个引用，回包只返回 basename 摘要
- `metadata`：小型 object，深度最多 3，序列化后最多 8 KiB

event_type 白名单：

- `perception.detected_object`
- `route.frame`
- `route.pose`
- `elevator.door_state`
- `elevator.floor_evidence`
- `task.failure`
- `task.recovery`
- `operator.note`

成功响应固定：

- `schema=trashbot.o6.archive_events.v1`
- `schema_version=1`
- `source=local_mock_event_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_event_written=true`

幂等键是 `task_id + event_id`。全新批次返回 `201/write_status=created/duplicate=false`；命中任一已有 `event_id` 返回 `200/write_status=updated/duplicate=true`，并在 `event_summary.created_count/updated_count` 给出混合批次摘要。

### GET /api/o6/archive/events

支持 query：

- `robot_id`
- `task_id`
- `event_type`
- `from_ms`
- `to_ms`
- `limit`：默认 50，最大 200

返回：

- `schema=trashbot.o6.archive_events.v1`
- `source=local_mock_event_archive`
- `query`
- `events[]`
- `event_summary`

`events[]` 只返回白名单字段：`event_id/event_type/occurred_at_ms/source/pose/summary/severity/evidence_refs/metadata/created_at_ms/updated_at_ms`，并按 `occurred_at_ms` 升序排列。非法 `limit`、未知 `event_type`、非法时间窗、`unknown_task` 或 `unauthorized_task` 都 fail-closed。

### POST /api/o6/archive/evidence

请求必须包含：

- `robot_id`
- `task_id`
- `evidence_refs[]`：1 到 64 条

每条 evidence ref 必须包含：

- `evidence_id`：task 内幂等键，长度 1 到 128
- `evidence_type`：必须是白名单类型
- `evidence_ref`：对象引用或 mock ref；服务端只保存 basename 摘要，不保存图片/视频/音频原始内容
- `captured_at_ms`：必须落在 task 时间窗内

可选字段：

- `event_id`
- `content_type`
- `size_bytes`
- `checksum`
- `metadata`：小型 object，深度最多 3，序列化后最多 8 KiB

evidence_type 白名单：

- `camera_frame`
- `snapshot`
- `route_frame`
- `elevator_frame`
- `failure_snapshot`
- `audio_clip`
- `log_excerpt`

成功响应固定：

- `schema=trashbot.o6.archive_evidence.v1`
- `schema_version=1`
- `source=local_mock_evidence_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `real_oss_upload_success=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_evidence_written=true`

幂等键是 `task_id + evidence_id`。全新批次返回 `201/write_status=created/duplicate=false`；命中任一已有 `evidence_id` 返回 `200/write_status=updated/duplicate=true`。

### GET /api/o6/archive/evidence

支持 query：

- `robot_id`
- `task_id`
- `evidence_type`
- `event_id`
- `limit`：默认 50，最大 200

返回：

- `schema=trashbot.o6.archive_evidence.v1`
- `source=local_mock_evidence_archive`
- `query`
- `evidence_refs[]`
- `evidence_summary`

`evidence_refs[]` 只返回白名单字段：`evidence_id/evidence_type/evidence_ref/captured_at_ms/event_id/content_type/size_bytes/checksum/metadata/created_at_ms/updated_at_ms`。它不返回 credential URL、token、base64、原始图片、原始音频、原始视频、完整日志或完整模型响应。写入后 `GET /api/o6/archive/tasks/<task_id>` 仍能在兼容 `events[]` / `evidence_refs[]` 中读到对应摘要。

### fail-closed 规则（Events/Evidence）

以下场景返回 4xx，且不得写入任何 event/evidence：

- bad JSON、非对象 JSON、空 body
- 缺少 `robot_id/task_id/events/evidence_refs` 或必填 item 字段
- `events[]` / `evidence_refs[]` 非数组、为空或超过 64
- `unknown_task`
- `unauthorized_task`
- 非白名单 `event_type` / `evidence_type`
- `occurred_at_ms` / `captured_at_ms` 越过 task 时间窗
- `metadata` 非 object、超深、超长或含 unsafe content
- payload 含 `Authorization`、`Bearer`、`token`、`password`、`secret`、`private_key`、credential URL、`/cmd_vel`、串口路径、`baudrate`、`traceback`
- payload 含 base64、原始图片/视频/音频、完整日志、完整模型响应或 raw content
- payload 声明真实能力，例如 `success=true`、`production_ready=true`、`cloud_db_connected=true`、`oss_uploaded=true`、`robot_control_executed=true`、`delivery_success=true`

## O6 local/mock 模型推理 contract

`POST /api/o6/archive/inference` 是 O6-KR5 的 local/mock 模型推理写入口。它复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 和 `FileBackedO6CloudArchiveStore`，只允许把推理结果写入已存在 archive task 的 `events[]`，不创建孤儿 inference record。

### Request Contract（POST）

必填字段：

- `robot_id`
- `task_id`
- `inference_id`
- `model_family`
- `requested_outputs`
- `inputs`

`requested_outputs[]` 当前上限是 8，但首批只允许：

- `elevator_door_state`
- `floor_recognition`

`inputs[]` 当前上限是 16。每条 input 必须包含：

- `input_id`
- `input_type`：`image_ref | frame_ref | snapshot_ref | metadata_only`
- `evidence_ref`
- `captured_at_ms`
- `metadata`：可选小型 JSON object 摘要，不能包含原始图片、凭证、完整模型返回体或真实能力声明

### Response Contract（POST）

所有成功响应固定：

- `schema=trashbot.o6.model_inference.v1`
- `schema_version=1`
- `source=local_mock_inference`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `real_gpu_model_connected=false`
- `real_external_model_api_connected=false`
- `real_model_inference_success=false`
- `real_floor_recognition_proven=false`
- `real_elevator_door_state_proven=false`
- `archive_event_written=true`

成功响应还包含：

- `write_status`：`created | updated`
- `duplicate`：首次写入 `false`，命中任一既有幂等键时 `true`
- `task_id`
- `robot_id`
- `inference_id`
- `results[]`
- `result_summary`
- `not_proven`

### Archive event contract

每个 `input + requested_output` 组合写成一条 task event：

- `event_type=model_inference.elevator_door_state`
- `event_type=model_inference.floor_recognition`

事件白名单字段包含：

- `event_id`
- `event_type`
- `timestamp_ms`
- `occurred_at_ms`
- `source=local_mock_inference`
- `inference_id`
- `input_id`
- `input_type`
- `model_family`
- `result_type`
- `result_value`
- `confidence`
- `evidence_ref`
- `metadata`
- `not_proven`

当前 deterministic local/mock stub 固定返回 `result_value=unknown` 与 `confidence=0.0`。这只证明 API、幂等、事件落库和读取链路，不证明真实 GPU、真实外部模型、真实楼层识别或真实电梯门状态。

### Duplicate Semantics（Inference）

幂等键：`task_id + inference_id + input_id + result_type`。

- 全新结果：`201` + `write_status=created` + `duplicate=false`
- 已有结果：`200` + `write_status=updated` + `duplicate=true`
- 混合批次：只要命中任一旧键即返回 `updated`，`result_summary.created_count/updated_count` 给出批内摘要

### Fail-Closed / 安全告警（Inference）

以下场景返回 fail-closed，且不得写入 `events[]`：

- 坏 JSON / 非对象 JSON / 空 body
- 缺少 `robot_id`、`task_id`、`inference_id`、`model_family`、`requested_outputs[]`、`inputs[]`
- `requested_outputs[]` 或 `inputs[]` 不是数组、为空或超过上限
- 未知 output 或 unsupported `input_type`
- `unknown_task`
- `unauthorized_task`
- `captured_at_ms` 不在 task `started_at_ms..finished_at_ms` 窗口内
- `metadata` 非小型 object 或包含 unsafe content
- unsafe content（`Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / `baudrate` / `traceback` / 凭证 URL）
- 真实能力声明（如 `success=true`、`production_ready=true`、`gpu_connected=true`、`external_model_connected=true`、`floor_recognition_proven=true`、`elevator_door_state_proven=true`、`robot_control_executed=true`）

## O6 local/mock tunnel online status contract

`POST /api/o6/tunnel/heartbeat`、`GET /api/o6/tunnel/robots`、`GET /api/o6/tunnel/robots/<robot_id>` 为 O6-KR1 增补本地/文件化隧道观测入口，和既有 archive/labels/inference 共用同一套 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`。

### POST /api/o6/tunnel/heartbeat

必填字段：

- `robot_id`
- `tunnel_provider`（`frp` / `wireguard` / `ngrok` / `mock`）

可选字段：

- `endpoint`：可选上报 endpoint，必须脱敏保存/返回，不回显 credential token/secret/password/private_key/Authorization
- `observed_at`：可选，支持整数毫秒或 ISO8601；缺省用服务端当前毫秒
- `ttl_seconds`：可选，默认 `300`，范围 `60~86400`
- `metadata`：可选，仅允许 `ip_family / network_type / region / notes`

失败场景（fail-closed）：

- bad JSON、bad body
- 缺字段
- `tunnel_provider` 不在白名单
- `metadata` 非 object、超字段长度、非法 key
- `endpoint`/`metadata` 含 unsafe content（包含 `Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / `baudrate` / `traceback` / credential URL）

成功响应固定：

- `schema=trashbot.o6.tunnel_status.v1`
- `schema_version=1`
- `source=local_mock_tunnel_status`
- `proof_status=not_proven`
- `real_tunnel_connected=false`
- `real_4g_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `safe_to_control=false`
- `robot_id`
- `status`
- `last_seen_at_ms`
- `ttl_seconds`
- `observed_at_ms`
- `endpoint`
- `tunnel_provider`
- `metadata`

### GET /api/o6/tunnel/robots

查询参数：

- `status=online|offline|all`（默认 `all`）
- `provider=<frp|wireguard|ngrok|mock>`（可选）
- `limit`（默认 50，最大 100）

响应是按 `last_seen_at_ms` 倒序的列表，返回：

- `robots[]`
- `total_robots`
- `query`（`status`/`provider`/`limit`）
- `updated_at_ms`

### GET /api/o6/tunnel/robots/<robot_id>

- 存在则返回该 robot 的单机快照（同上字段）
- 不存在返回 `404 + error.code=not_found`

### 安全边界

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
