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
- `labeling_queue_inspector`：KR4 只读标注队列检查视图，状态为 `fixture_labeling_ready | blocked_not_proven`
- `voice_asr_tts_inspector`：KR5 只读 ASR/TTS 检查视图，状态为 `fixture_voice_ready | blocked_not_proven`
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

## UI Boundary

`O7 Previews` tab 的 `Cloud Archive Tasks` 区块默认不读取本地路径。只有点击 `Load archive tasks` 才调用该 GET query。

UI 只展示任务列表、最近任务、selected task、安全摘要、fixed false fields、blocked reasons 和 not proven。不得提供播放、提交、导出、发送、控制、停止、取消或恢复类动作按钮。

UI 同时展示 `route_replay_inspector` 的 selected task、map frame、frame count、sample frames 表格、event timeline、keyframe refs 和 cursor 初始 false 字段。该区域只用于 operator 检查历史路线 fixture 是否具备逐帧位置、速度和状态转移槽位，不提供任何逐帧驱动或机器人动作入口。

UI 同时展示 `labeling_queue_inspector` 的 selected task、review item count、sample review items、label schema、allowed label types、draft labels、dataset export gaps 和标注相关 false fields。该区域只用于 operator 检查 archive fixture 是否具备 O7-KR4 标注队列数据形状，不提供提交、回滚、导出、发送、控制、播放、停止、取消或恢复类动作入口。

UI 同时展示 `voice_asr_tts_inspector` 的 selected task、voice session、ASR event sample、latest partial/final、TTS draft summary、speaker dispatch summary、media preflight dependency 和语音相关 false fields。该区域只用于 operator 检查 archive fixture 是否具备 O7-KR5 ASR/TTS 调试数据形状，不提供 Send、Speak、Play、Dispatch、Control、Stop、Cancel、Recovery、Submit、Export 或等价动作入口。

## O7 Impact

本接口推动 O7 的方式是建立统一数据源雏形：KR3 可以消费 trajectory/events，KR4 可以消费 labels，KR5 可以消费 voice，KR6 可以消费 command envelope 摘要。但它仍是 software proof，不提升真实 O7 完成度，不证明真实云端、机器人、语音、标注或控制能力。
