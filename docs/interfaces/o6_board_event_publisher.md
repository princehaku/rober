# O6 Board Event Publisher

## Scope

机器人侧 O6 board event publisher 位于 `ros2_trashbot_behavior.archive_event_publisher`，负责把 `task_record` 中的任务状态、电梯状态、路线帧、关键帧、检测结果和失败原因整理成 Task A `/api/o6/archive/events` 可接收的 event envelope。

当前实现是 software proof path：

- 不启动真实硬件；
- 不假设 UART、摄像头、4G、公网或真实 OSS 已可用；
- 默认写本地 JSONL 队列，不访问网络；
- 可选配置 `o6_archive_base_url` 后才尝试 POST `/api/o6/archive/events`；
- POST 失败时保留本地 retry stub，不阻塞机器人 action result。

## Event Envelope

每条事件固定包含：

- `robot_id`
- `task_id`
- `event_id`
- `event_type`
- `timestamp`
- `created_at`
- `evidence_ref`
- `source=software_proof`
- `proof_status=not_proven`
- `evidence_boundary=software_proof_o6_board_event_publisher`
- `payload`

`created_at` 与 `timestamp` 保持同值，兼容 Task A 文档中的 archive event schema 和机器人侧显式时间字段。

## Event Types

- `task_status`：终态、目标点、状态转移数量和任务时长。
- `elevator_state`：电梯 dry-run/辅助阶段、目标楼层、人工介入标记。
- `route_frame`：`route_progress`、导航尝试数和路线证据引用。
- `keyframe`：路线关键帧目录或显式 keyframe 引用。
- `detection_result`：`detection_snapshot_refs` 中的感知快照引用。
- `failure_reason`：失败、取消或错误码对应的可读原因。

## Task Orchestrator Parameters

`task_orchestrator` 写入 `task_record` 后会调用 O6 publisher：

- `o6_archive_events_enabled`：默认 `true`。
- `o6_archive_robot_id`：默认 `trashbot-dev`。
- `o6_archive_queue_file`：默认空；为空时写到 `task_record_dir/o6_archive_events.jsonl`。
- `o6_archive_base_url`：默认空；为空时只写本地队列。
- `o6_archive_bearer_token_env`：默认 `TRASHBOT_O6_ARCHIVE_TOKEN`。

## Local Queue

本地队列是 JSONL，每行包含：

- `queued_at`
- `delivery_status=queued`
- `retry_stub.reason`
- `retry_stub.last_error`
- `event`

该队列只证明机器人侧能生成并保留 O6 上报事件，不证明云端已收到、生产 DB 已持久化、真实 4G 可用、真实 OSS 上传成功或现场送达成功。
