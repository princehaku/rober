# O6 Event Evidence Archive PRD

## 需求概述

本轮设计 O6 任务内事件与证据引用的增量存档 API。目标是在已有 `POST /api/o6/archive/tasks` 的基础上，补齐任务运行过程中的追加写入和查询能力：

- `POST /api/o6/archive/events`
- `GET /api/o6/archive/events`
- `POST /api/o6/archive/evidence`
- `GET /api/o6/archive/evidence`

这是 local/mock software proof 阶段的产品合同，不代表真实云数据库、真实 OSS、真实公网、真实 4G 或机器人控制已经接通。

## 目标用户

- Orange Pi / 上位机软件：任务创建后可持续追加感知、路线、电梯、失败和恢复事件。
- O7 PC 运营与数据训练平台：可以按 task timeline 查询事件和 evidence refs，用于路线回放、标注、失败复盘。
- Product/QA：通过固定 `schema/source/proof_status` 与真实能力 false 字段，避免把本地 mock 数据误解为 production 成功。

## 用户价值

1. 任务不再只有一次性快照，而是有可追溯 timeline。
2. 证据大对象和数据库记录解耦：API 只存 `evidence_ref`，不把图片/视频/音频塞进 JSON。
3. O7 后续可以从统一 O6 数据源拉取 route replay、elevator evidence、failure evidence 和 labeling seed。
4. 失败事件与证据引用同 task 绑定，便于售后、复盘和模型改进。

## OKR 映射

- `O6-KR2`：任务记录和感知事件持久化存档，支持按 `robot_id / task_id / date` 查询。
  - 本轮覆盖：事件追加写入、事件查询、事件类型白名单、task scope fail-closed。
- `O6-KR3`：摄像头帧/快照等大对象通过 OSS 存档，云端数据库只保留对象引用（`evidence_ref`）。
  - 本轮覆盖：evidence reference 写入与查询，固定 `real_oss_connected=false`，不上传大对象。

方向判断：继续 O6。O6 仍是最低完成度 Objective，且本轮是 O7 数据消费和失败复盘的直接前置。

## 范围内功能 P0

### 1) `POST /api/o6/archive/events`

#### 请求字段

顶层字段：

- `robot_id`：string，必填。
- `task_id`：string，必填，必须已存在于 archive task store。
- `events`：array，必填，1 到 64 条。

每条 event 必填字段：

- `event_id`：string，必填，task 内唯一。
- `event_type`：string，必填，必须在白名单内。
- `occurred_at_ms`：number，必填，必须落在 task 时间窗内；若 task `finished_at_ms` 为空，允许大于 `started_at_ms`。
- `source`：string，可选；默认 `local_mock_event_archive`。

每条 event 可选字段：

- `pose`：object，仅允许 `x_m`、`y_m`、`yaw_rad`、`floor_id`。
- `summary`：string，小文本摘要。
- `severity`：`info | warning | error`。
- `evidence_refs`：array，最多 8 个 `evidence_ref` 字符串。
- `metadata`：object，小型白名单摘要，不能包含原始图片、完整日志、凭证或真实能力声明。

#### event_type 白名单

- `perception.detected_object`
- `route.frame`
- `route.pose`
- `elevator.door_state`
- `elevator.floor_evidence`
- `task.failure`
- `task.recovery`
- `operator.note`

#### 响应字段

成功响应固定：

- `schema: trashbot.o6.archive_events.v1`
- `schema_version: 1`
- `source: local_mock_event_archive`
- `proof_status: not_proven`
- `safe_to_control: false`
- `delivery_success: false`
- `primary_actions_enabled: false`
- `pc_only: true`
- `connects_cloud_production: false`
- `real_cloud_db_connected: false`
- `real_oss_connected: false`
- `robot_control_executed: false`
- `archive_event_written: true`

同时返回：

- `write_status: created | updated`
- `duplicate: boolean`
- `task_id`
- `robot_id`
- `events_written[]`
- `event_summary`
- `not_proven[]`

#### 幂等语义

幂等键：`task_id + event_id`。

- 批次内全部新事件：`201` + `write_status=created` + `duplicate=false`。
- 命中任一已有事件：`200` + `write_status=updated` + `duplicate=true`。
- 混合批次：只要命中任一旧 `event_id`，整体响应为 updated，同时 `event_summary.created_count/updated_count` 给出批内摘要。

### 2) `GET /api/o6/archive/events`

查询参数：

- `robot_id`：可选；提供时必须与 task 归属一致。
- `task_id`：可选；若为空则返回最近事件摘要，仍必须受 `limit` 限制。
- `event_type`：可选，必须在 event_type 白名单内。
- `from_ms` / `to_ms`：可选时间窗。
- `limit`：可选，1 到 200，默认 50。

响应字段：

- 固定 `schema/source/proof_status` 与真实能力 false 字段。
- `query`
- `events[]`：只包含白名单字段。
- `event_summary`

排序：默认按 `occurred_at_ms` 升序，便于 route replay。若后续实现采用倒序，必须在实现文档说明原因。

### 3) `POST /api/o6/archive/evidence`

#### 请求字段

顶层字段：

- `robot_id`：string，必填。
- `task_id`：string，必填，必须已存在于 archive task store。
- `evidence_refs`：array，必填，1 到 64 条。

每条 evidence ref 必填字段：

- `evidence_id`：string，必填，task 内唯一。
- `evidence_type`：string，必填，必须在白名单内。
- `evidence_ref`：string，必填，只能是对象引用或 mock ref，不允许 credential URL。
- `captured_at_ms`：number，必填，必须落在 task 时间窗内；若 task `finished_at_ms` 为空，允许大于 `started_at_ms`。

每条 evidence ref 可选字段：

- `event_id`：string，可选，用于关联事件。
- `content_type`：string，可选，如 `image/jpeg`、`text/plain`、`audio/wav`。
- `size_bytes`：number，可选，仅允许摘要值，不触发真实上传。
- `checksum`：string，可选，小型摘要。
- `metadata`：object，小型白名单摘要。

#### evidence_type 白名单

- `camera_frame`
- `snapshot`
- `route_frame`
- `elevator_frame`
- `failure_snapshot`
- `audio_clip`
- `log_excerpt`

#### 响应字段

成功响应固定：

- `schema: trashbot.o6.archive_evidence.v1`
- `schema_version: 1`
- `source: local_mock_evidence_archive`
- `proof_status: not_proven`
- `safe_to_control: false`
- `delivery_success: false`
- `primary_actions_enabled: false`
- `pc_only: true`
- `connects_cloud_production: false`
- `real_cloud_db_connected: false`
- `real_oss_connected: false`
- `real_oss_upload_success: false`
- `robot_control_executed: false`
- `archive_evidence_written: true`

同时返回：

- `write_status: created | updated`
- `duplicate: boolean`
- `task_id`
- `robot_id`
- `evidence_refs_written[]`
- `evidence_summary`
- `not_proven[]`

#### 幂等语义

幂等键：`task_id + evidence_id`。

- 批次内全部新 evidence：`201` + `write_status=created` + `duplicate=false`。
- 命中任一已有 evidence：`200` + `write_status=updated` + `duplicate=true`。
- 混合批次按 updated 响应，并返回 created/updated 计数。

### 4) `GET /api/o6/archive/evidence`

查询参数：

- `robot_id`：可选。
- `task_id`：可选。
- `evidence_type`：可选，必须在 evidence_type 白名单内。
- `event_id`：可选。
- `limit`：可选，1 到 200，默认 50。

响应字段：

- 固定 `schema/source/proof_status` 与真实能力 false 字段。
- `query`
- `evidence_refs[]`：只包含白名单摘要，不包含原始大对象、不包含 token、不包含 credential URL。
- `evidence_summary`

## Fail-Closed 规则

以下场景必须拒绝，且不得写入任何事件或 evidence：

- bad JSON、非对象 JSON、空 body。
- `events[]` 或 `evidence_refs[]` 非数组、为空或超过上限。
- 缺少必填字段。
- `unknown_task`：task 不存在。
- `unauthorized_task`：`robot_id` 与 task 归属不一致。
- `event_type` 或 `evidence_type` 不在白名单。
- `occurred_at_ms` / `captured_at_ms` 不在 task 时间窗内。
- `metadata` 非小型 object、超深、超长或含 unsafe content。
- 输入包含 `Authorization`、`Bearer`、`token`、`password`、`secret`、`private_key`、credential URL、`/cmd_vel`、串口路径、`baudrate`、`traceback`。
- 输入声明真实能力，如 `success=true`、`production_ready=true`、`oss_uploaded=true`、`cloud_db_connected=true`、`robot_control_executed=true`。

## 范围外

- 不实现真实 OSS 上传、STS 凭证、CDN 分发或真实对象探测。
- 不接入 production DB/queue、TLS、公网、4G。
- 不触碰硬件配置、WAVE ROVER、UART、串口、ROS launch、Nav2。
- 不新增手机/PC UI。
- 不执行机器人控制，不暴露 `/cmd_vel`。

## 优先级和验收口径

P0 必须满足：

- 四个 endpoint 的 request/response/fail-closed/幂等语义齐全。
- 成功响应固定 `schema/source/proof_status` 与真实能力 false 字段。
- 查询接口按 `robot_id/task_id/event_type/evidence_type` 能返回白名单摘要。
- 所有写入只允许附着在已有 task。

P1 实现阶段必须满足：

- 单元测试覆盖所有 P0 成功与失败路径。
- 接口文档、PC 产品文档、cloud-relay README 同步。
- 无硬件、ROS launch、真实 SSH 上车配置改动。

## 责任 Owner

- `product-okr-owner`：本轮设计、验收口径与证据边界。
- `full-stack-software-engineer`：后续实现、测试、文档同步和 `tech-done/side2side/final` 收口。

## 风险与证据边界

- 这只是 local/mock contract，不能提升为真实 O6 production backend ready。
- `archive_event_written=true` 或 `archive_evidence_written=true` 只表示本地 file-backed store 写入成功。
- `evidence_ref` 存在不等于对象真实存在、OSS 上传成功或 CDN 可读。
- 后续 O7/手机消费必须展示 `proof_status=not_proven` 和真实能力 false 字段，不能把 mock timeline 当真实现场证据。
