# O7 Cloud Archive Task API

## Scope

`GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>` 是 `pc-tools/workstation` 的 PC-only read-only 本地 fixture 入口。它读取 operator 显式指定的 `trashbot.o7.cloud_archive_fixture.v1` JSON，把任务列表和 KR3/KR4/KR5/KR6 相关数据压成安全摘要。

该接口不连接 O6 真实云归档，不连接 realtime、annotation、voice 或 command API，不读取 ROS2 graph，不打开串口，不发送 TTS、手控、寻路或任何机器人命令。

`remote_cloud_relay.py` 同时暴露 `GET /api/o7/cloud-archive/tasks` 的 cloud relay HTTP 只读 contract。该 cloud relay 版本不要求 bearer，不读取真实 archive store，当前固定返回 `archive_status=blocked_not_proven`、空任务列表、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有控制/语音/标注危险字段 false。它只是让 PC 从本地 fixture 迈向 cloud relay HTTP contract 的 schema proof，不等于真实云 archive。

PC 端新增 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<local-loopback-url>`。该 probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]`，由 Node 后端拉取远端 `/api/o7/cloud-archive/tasks`，检查 schema、task count、selected/latest、inspector 状态、危险 true 字段、blocked/not_proven。它不接受远程 URL、不带 bearer、不连接公网云、不读取硬件、不发送命令。

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
- cloud relay contract 还必须固定 `playback_available=false`、`submit_enabled=false`、`real_robot_ack_connected=false`、`real_asr_tts_runtime_connected=false`

核心摘要：

- `archive_status=fixture_archive_ready | blocked_not_proven`
- `input_status.archive_json/status/failure_reason`
- `task_list.total_tasks/tasks[]`
- `selected_task`
- `latest_task`
- `safe_summaries.trajectory/events/labels/voice/commands`
- `route_replay_inspector`：KR3 只读逐帧检查视图，状态为 `fixture_inspector_ready | blocked_not_proven`
- `labeling_queue_inspector`：KR4 只读标注队列检查视图，状态为 `fixture_labeling_ready | blocked_not_proven`
- `voice_asr_tts_inspector`：KR5 只读 ASR/TTS 检查视图，状态为 `fixture_voice_ready | blocked_not_proven`
- `safe_command_inspector`：KR6 只读手控/寻路检查视图，状态为 `fixture_command_ready | blocked_not_proven`
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

`labeling_queue_inspector` 只从 selected task 的本地 fixture 白名单字段生成，不透传完整原始 payload：

- `selected_task_id`、`review_item_count`
- `sample_review_items` 最多 5 条，每条包含 `item_id`、`task_id`、`frame_id`、脱敏 `media_ref`、脱敏 `evidence_ref`、`current_labels.count` 和最多 3 条 label sample
- label sample 只包含 `label_type`、`value`、`status`、脱敏 `evidence_ref`
- `label_schema.schema_ref/version/required_fields/allowed_fields`，其中字段列表最多 5 个
- `allowed_label_types` 最多 5 条
- `draft_labels.count/sample/autosave_available=false`，draft sample 最多 5 条
- `dataset_export.available=false`、`status=blocked_not_available | fixture_summary_only`、脱敏 `export_ref`、最多 5 个 `supported_formats`、最多 5 个 `gaps`
- `submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`
- 自带 `blocked_reasons` 和 `not_proven`

兼容性规则：

- selected task 内有 `review_items[]` 时，以 `review_items[]` 生成 `sample_review_items`，并从每个 item 的 `current_labels[]` 或 `labels[]` 生成当前 label sample。
- selected task 只有 `labels[]` 时，adapter 会把每条 label 派生成最小 review item 和 draft label 摘要，保证 KR4 UI 能检查 item/media/label type/value/evidence_ref，而不是只看到 label count。
- selected task 没有 `review_items[]` 且没有 `labels[]` 时，`labeling_queue_inspector.status=blocked_not_proven` 且样本为空。

`voice_asr_tts_inspector` 只从 selected task 的本地 fixture 白名单字段生成，不连接真实 ASR/TTS runtime，不发送 TTS，不调度喇叭：

- `selected_task_id`
- `voice_session.session_id/source/evidence_ref/audit_refs/status`
- `asr_event_count`
- `sample_asr_events` 最多 5 条，每条包含 `event_type`、`timestamp_ms`、脱敏 `transcript`、`confidence`、脱敏 `evidence_ref`
- `latest_partial` 和 `latest_final`，每个槽位包含 `text`、`timestamp_ms`、`confidence`、`evidence_ref`、`status`
- `tts_draft.text/text_length/voice_profile/language/confirmation_required/status`，`text` 是脱敏后的安全文本摘要，不代表已发送
- `speaker_dispatch.sends_to_robot=false`、`speaker_dispatch_enabled=false`、`ack_status`、`speaker_ack_ref`、`failure_event_ref`、最多 5 条 `failure_refs`
- `media_preflight_dependency.required=true/source_schema/status/dependency_ref/gaps`
- 固定 `asr_stream_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`
- 自带 `blocked_reasons` 和 `not_proven`

兼容性规则：

- selected task 内有 `asr_events[]` 时，adapter 从完整事件列表计算 latest partial/final，但 sample 最多只返回 5 条。
- selected task 支持 `tts_drafts[]`，也兼容旧式 `tts_draft` 单对象；`voice_profile` 可来自 draft 或 task 级 `voice_profile`。
- `voice_session`、`speaker_ack`、`media_preflight` 均为可选对象，缺失时仍返回 fail-closed 缺口字段。
- transcript、TTS text、gap 和 evidence/media 引用都必须脱敏；绝对路径只保留 basename。
- selected task 没有 `asr_events[]` 且没有 `tts_draft(s)` 时，`voice_asr_tts_inspector.status=blocked_not_proven` 且样本为空。

`safe_command_inspector` 只从 selected task 的本地 fixture 白名单字段生成，不连接真实 command API，不发送手控/寻路命令，不绑定键盘，不读取地图点击：

- `selected_task_id`
- `command_session.command_session_id/source/evidence_ref/audit_refs/status`
- `command_count`
- `sample_commands` 最多 5 条，每条只包含 `command_id`、`command_type`、`status`、脱敏 `envelope_ref`、脱敏 `idempotency_key_ref`、脱敏 `evidence_ref`
- `manual_turn_envelope.sends_to_robot=false`、`requested_direction`、`velocity_limited=true`、`steering_limited=true`、脱敏 `evidence_ref`、`status`
- `navigate_goal_envelope.sends_to_robot=false`、`goal_source`、`map_frame`、`x_m/y_m/yaw_rad`、脱敏 `evidence_ref`、`status`
- `velocity_limits.max_linear_mps/max_angular_radps/source/hardware_verified=false/status`
- `steering_limits.max_steering_angle_rad/max_turn_rate_radps/source/hardware_verified=false/status`
- `map_goal_slot.map_frame/x_m/y_m/yaw_rad/status/evidence_ref`
- `idempotency_key_requirement.required=true/header=Idempotency-Key/key_ref/status`
- `confirmation_policy.manual_turn_requires_confirmation=true`、`navigate_goal_requires_confirmation=true`、`keyboard_control_requires_hold=true`、`status`
- `robot_ack_blocked_summary.ack_status=blocked_not_proven`、`last_command_id`、`ack_ref`、`timeout_ms`、`cancel_ack_ref`、`stop_ack_ref`、`recovery_ref`、`status=blocked_not_proven`
- `evidence_gaps` 必须保留 `robot_ack_timeout_trace_missing`、`cancel_ack_trace_missing`、`stop_ack_trace_missing`、`recovery_event_trace_missing`
- 固定 `command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`
- 自带 `blocked_reasons` 和 `not_proven`

兼容性规则：

- selected task 可直接提供 task 级 `command_session`、`manual_turn_envelope`、`navigate_goal_envelope`、`velocity_limits`、`steering_limits`、`map_goal_slot`、`idempotency_key_requirement`、`confirmation_policy`、`robot_ack_status` 或 `command_ack`。
- selected task 的 `commands[]` 只用于生成限量 sample，不透传 command payload，不触发任何发送、重放、取消、停止或恢复动作。
- selected task 没有 `commands[]` 且没有 `manual_turn_envelope` / `navigate_goal_envelope` 时，`safe_command_inspector.status=blocked_not_proven` 且 `sample_commands=[]`。

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
- 声称 `real_asr_tts_runtime_connected=true`、`asr_stream_connected=true`、`tts_send_enabled=true` 或 `speaker_dispatch_enabled=true`
- 声称 `manual_control_enabled=true`、`navigate_goal_enabled=true`、`keyboard_control_enabled=true` 或 `real_robot_ack_connected=true`

## UI Boundary

`O7 Previews` tab 的 `Cloud Archive Tasks` 区块默认不读取本地路径。只有点击 `Load archive tasks` 才调用该 GET query。

同一 tab 的 `Cloud archive tasks probe` 区块默认只填本机回环示例 URL，不自动发起请求。点击 `Probe cloud archive tasks` 后才调用 PC 后端 probe API；浏览器不直接访问 relay。UI 展示 probe status、source base URL、remote schema、archive status、task count、selected/latest、四个 inspector 状态、dangerous true fields、关键 false fields、blocked reasons 和 not proven。

UI 只展示任务列表、最近任务、selected task、安全摘要、fixed false fields、blocked reasons 和 not proven。不得提供自动播放、提交、导出、发送、控制、停止、取消或恢复类动作按钮。

UI 同时展示 `route_replay_inspector` 的 selected task、map frame、frame count、sample frames 表格、event timeline、keyframe refs 和 cursor 初始 false 字段。该区域只用于 operator 检查历史路线 fixture 是否具备逐帧位置、速度和状态转移槽位。

PC UI 在该区域提供本地 route replay player：`Previous frame`、`Next frame`、`Reset cursor` 和可选 range cursor 只改变浏览器内存中的 sample frame 下标，不调用任何 API，不写后端状态，不发送机器人命令，也不代表真实云历史路线回放。player 展示当前 cursor index、sample frame 总数、`timestamp_ms`、`x_m/y_m/yaw_rad`、`speed_mps`、`state` 和 `evidence_ref`。当 archive 未加载、没有 selected task、没有 sample frames、`route_replay_inspector.status!=fixture_inspector_ready`，或响应显式给出 `playback_available=false` 时，player 必须显示 `blocked_not_proven` 并禁用 frame navigation。即使本地 cursor 可浏览，也必须继续展示 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`cursor_initial_state.safe_to_play=false`、`real_cloud_archive_connected=false` 和 `robot_control_executed=false`。

UI 同时展示 `labeling_queue_inspector` 的 selected task、review item count、sample review items、label schema、allowed label types、draft labels、dataset export gaps 和标注相关 false fields。该区域只用于 operator 检查 archive fixture 是否具备 O7-KR4 标注队列数据形状，不提供提交、回滚、导出、发送、控制、播放、停止、取消或恢复类动作入口。

PC UI 在该区域提供本地 labeling review panel：加载 archive 后默认聚焦第一条 `sample_review_items`，`Previous item`、`Next item` 和 `Reset item` 只改变浏览器内存中的 item cursor，不调用任何 API，不写后端状态，不提交标注，不回滚标注，不导出训练集，也不发送机器人命令。panel 展示当前 item 的 `item_id`、`frame_id`、`media_ref`、`evidence_ref`、current label count、current label sample，以及 draft label sample、allowed label types 和 label schema 摘要；同时必须继续显式展示 `submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`、`draft_labels.autosave_available=false`。当 archive 未加载、selected task 缺失、sample review items 为空，或 `labeling_queue_inspector.status!=fixture_labeling_ready` 时，panel 必须显示 `blocked_not_proven` 并禁用 item navigation。该 panel 不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave、真实训练集导出或 O7-KR4 完成。

UI 同时展示 `voice_asr_tts_inspector` 的 selected task、voice session、ASR event sample、latest partial/final、TTS draft summary、speaker dispatch summary、media preflight dependency 和语音相关 false fields。该区域只用于 operator 检查 archive fixture 是否具备 O7-KR5 ASR/TTS 调试数据形状，不提供 Send、Speak、Play、Dispatch、Control、Stop、Cancel、Recovery、Submit、Export 或等价动作入口。

UI 同时展示 `safe_command_inspector` 的 command session、sample commands、manual turn envelope、navigate goal envelope、velocity/steering limits、map goal slot、idempotency key requirement、confirmation policy、robot ACK blocked summary、evidence gaps 和 KR6 false fields。该区域只用于 operator 检查 archive fixture 是否具备 O7-KR6 手控/寻路契约数据形状，不提供 Send、Run、Control、Play、Submit、Export、Stop、Cancel、Recovery、Navigate、Dispatch、Speak 或等价动作入口。

## O7 Impact

本接口推动 O7 的方式是建立统一数据源雏形：KR3 可以消费 trajectory/events，KR4 可以消费 labels，KR5 可以消费 voice，KR6 可以消费 selected task 级 command envelope 和 ACK 缺口检查视图。cloud relay HTTP 只读 contract 只证明 endpoint shape 可由 relay 暴露；它仍是 software proof，不提升真实 O7 完成度，不证明真实云端、机器人、语音、标注、路线回放或控制能力。
