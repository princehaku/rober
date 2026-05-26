# O7 Cloud Archive Task API

## Scope

`GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>` 是 `pc-tools/workstation` 的 PC-only read-only 本地 fixture 入口。它读取 operator 显式指定的 `trashbot.o7.cloud_archive_fixture.v1` JSON，把任务列表和 KR3/KR4/KR5/KR6 相关数据压成安全摘要。

该接口不连接 O6 真实云归档，不连接 realtime、annotation、voice 或 command API，不读取 ROS2 graph，不打开串口，不发送 TTS、手控、寻路或任何机器人命令。

## Response Contract

固定字段：

- `schema=trashbot.o7.cloud_archive_tasks.v1`
- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_archive_connected=false`
- `real_realtime_api_connected=false`
- `real_annotation_api_connected=false`
- `real_voice_api_connected=false`
- `real_command_api_connected=false`
- `robot_control_executed=false`

核心摘要：

- `archive_status=fixture_archive_ready | blocked_not_proven`
- `input_status.archive_json/status/failure_reason`
- `task_list.total_tasks/tasks[]`
- `selected_task`
- `latest_task`
- `safe_summaries.trajectory/events/labels/voice/commands`
- `route_replay_inspector`：KR3 只读逐帧检查视图，状态为 `fixture_inspector_ready | blocked_not_proven`
- `fixed_false_fields`
- `blocked_reasons`
- `not_proven`

`route_replay_inspector` 只从 selected task 的本地 fixture 白名单字段生成，不透传完整原始 payload：

- `selected_task_id`、`map_frame`、`frame_count`
- `sample_frames` 最多 5 帧，每帧包含 `frame_index`、`timestamp_ms`、`x_m`、`y_m`、`yaw_rad`、`speed_mps`、`state`、脱敏 `evidence_ref`
- `event_timeline` 最多 5 条，每条包含 `event_type`、`state`、`timestamp_ms`、脱敏 `evidence_ref`
- `keyframe_refs` 最多 5 条，引用只保留安全 basename
- `cursor_initial_state.playing=false`、`safe_to_play=false`、`speed=0`、`frame_index` 为首个 sample frame 或 `null`
- 自带 `blocked_reasons` 和 `not_proven`

## Fail-Closed Rules

以下输入必须返回 `archive_status=blocked_not_proven`：

- 空 `archiveJson`
- 文件缺失或读取失败
- 坏 JSON 或顶层非 object
- `schema` 不是 `trashbot.o7.cloud_archive_fixture.v1`
- 包含凭证、串口、`/cmd_vel`、traceback 或本机绝对路径等 unsafe copy
- 声称 delivery/dropoff/cloud archive success/ready/connected
- 声称 `safe_to_control=true`、`primary_actions_enabled=true`、`robot_control_executed=true` 或 command dispatch enabled
- 声称真实 cloud/realtime/annotation/voice/command API connected

## UI Boundary

`O7 Previews` tab 的 `Cloud Archive Tasks` 区块默认不读取本地路径。只有点击 `Load archive tasks` 才调用该 GET query。

UI 只展示任务列表、最近任务、selected task、安全摘要、fixed false fields、blocked reasons 和 not proven。不得提供播放、提交、导出、发送、控制、停止、取消或恢复类动作按钮。

UI 同时展示 `route_replay_inspector` 的 selected task、map frame、frame count、sample frames 表格、event timeline、keyframe refs 和 cursor 初始 false 字段。该区域只用于 operator 检查历史路线 fixture 是否具备逐帧位置、速度和状态转移槽位，不提供任何逐帧驱动或机器人动作入口。

## O7 Impact

本接口推动 O7 的方式是建立统一数据源雏形：KR3 可以消费 trajectory/events，KR4 可以消费 labels，KR5 可以消费 voice，KR6 可以消费 command envelope 摘要。但它仍是 software proof，不提升真实 O7 完成度，不证明真实云端、机器人、语音、标注或控制能力。
