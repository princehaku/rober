# O7 Realtime Operator Console Contract

## Scope

`trashbot.o7.operator_console.v1` 是 O7 PC 运营调试平台的最小 cloud-contract driven 契约。它用于让 `pc-tools/workstation` 先展示六个 KR 的界面骨架和阻塞原因，同时保持真实机器人链路关闭。

当前实现位置：

- cloud helper：`cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py::build_o7_operator_console_contract()`
- PC API：`GET /api/o7/operator-console`
- PC acceptance guard：`GET /api/o7/operator-console/acceptance`
- PC fixture preview API：`GET /api/o7/route-replay-preview?fixtureJson=<local-json>`
- PC UI：`pc-tools/workstation` 的 `O7 Console` tab
- Board media preflight source contract：`docs/interfaces/o7_board_media_preflight.md`

## Fail-Closed Fields

所有响应必须包含并保持：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `cloud_api_status=draft_blocked_not_proven`
- `robot_connection=not_connected_by_pc`
- `operator_mode=observe_only`
- `board_media_preflight_required=true`
- `board_media_preflight_schema=trashbot.o7_board_media_preflight.v1`
- `board_media_preflight_state=blocked`
- `labeling_queue_snapshot.submit_enabled=false`
- `labeling_queue_snapshot.rollback_enabled=false`
- `labeling_queue_snapshot.real_annotation_api_connected=false`
- `labeling_queue_snapshot.dataset_export_available=false`
- `voice_asr_tts_snapshot.asr_stream_connected=false`
- `voice_asr_tts_snapshot.tts_send_enabled=false`
- `voice_asr_tts_snapshot.speaker_dispatch_enabled=false`
- `voice_asr_tts_snapshot.real_voice_api_connected=false`
- `voice_asr_tts_snapshot.real_asr_tts_runtime_connected=false`
- `safe_command_snapshot.command_dispatch_enabled=false`
- `safe_command_snapshot.manual_control_enabled=false`
- `safe_command_snapshot.navigate_goal_enabled=false`
- `safe_command_snapshot.keyboard_control_enabled=false`
- `safe_command_snapshot.real_command_api_connected=false`
- `safe_command_snapshot.real_robot_ack_connected=false`

PC 不直连机器人，不读取 ROS2 graph，不打开串口，不发送 WAVE ROVER、Nav2、TTS 或手控命令。

## Route Replay Fixture Preview

`trashbot.o7.route_replay_preview.v1` 是 O7-KR3 的 PC-only 本地 fixture 预览契约。它比 `route_replay_snapshot` 前进一步：允许 reviewer 通过 query path 指定一个本地安全 JSON fixture，并由 Node adapter 生成可消费的数据摘要。但它仍不是 O6 cloud archive、不是云端历史任务查询、不是真实逐帧回放，也不代表机器人运动或投放成功。

API：

- `GET /api/o7/route-replay-preview?fixtureJson=<local-json>`

支持的输入 schema：

- `schema=trashbot.o7.route_replay_fixture.v1`
- 可选字段：`task_id`、`robot_id`、`route_id`、`map_frame`、`trajectory_frames[]`、`keyframe_refs[]`、`state_transitions[]`、`evidence_ref`

固定 fail-closed 字段：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_archive_connected=false`
- `robot_control_executed=false`
- `playback_cursor_initial_state.playing=false`
- `playback_cursor_initial_state.speed=0`
- `playback_cursor_initial_state.safe_to_play=false`

输出只保留安全摘要：

- `task`：`task_id`、`robot_id`、`route_id` 和脱敏后的 `evidence_ref`
- `route_metadata`：`map_frame`、固定 `frame_schema=fixture_trajectory_frame_summary_v1`、`source=local_json_fixture`
- `trajectory`：`frame_count` 和最多 3 个 `sample_frames`
- `playback_cursor_initial_state`：只读初始游标，不允许播放或下发
- `keyframes`：`count` 和限量 `sample_refs`
- `evidence_refs`：fixture/task/keyframe 的安全引用
- `state_transitions`：`count`、限量 `sample` 和 `gaps`

Adapter 必须拒绝并返回 `preview_status=blocked_not_proven`：

- query 未提供、文件缺失、读取失败、坏 JSON、顶层不是 object
- `schema` 不是 `trashbot.o7.route_replay_fixture.v1`
- fixture 内含绝对路径、凭证、串口、`/cmd_vel`、traceback 或其他 unsafe copy
- fixture 声称 `delivery_success=true`、`playback_available=true`、delivery/dropoff/route replay success
- fixture 声称 `safe_to_control=true`、`primary_actions_enabled=true`、`robot_control_executed=true` 或 command dispatch enabled

该接口的 `fixture_preview_ready` 只表示本地 JSON 被压缩成安全摘要；它不提升 O7 完成度，不证明真实历史任务列表、真实轨迹 API、真实关键帧归档、真实状态转移时间线、真实云端归档、真实 playback cursor、真实机器人控制或真实 delivery success。

## Acceptance Guard

`trashbot.o7.operator_console_acceptance.v1` 是从 `buildO7OperatorConsoleResponse()` 派生的只读验收摘要，用于防止 O7 Console 的 fail-closed 契约在后续修改中漂移。它不是新的实机能力，不读取硬件、不发送命令、不连接云端生产，也不提升 O7 完成度。

固定边界：

- `source_response_schema=trashbot.o7.operator_console.v1`
- `source_endpoint=/api/o7/operator-console`
- `guard_endpoint=/api/o7/operator-console/acceptance`
- `evidence_boundary=software_proof_o7_operator_console_acceptance_guard`
- `reads_hardware=false`
- `sends_commands=false`
- `connects_cloud_production=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_real_capability_proof=true`

Guard 必须自动复核：

- O7-KR1 到 O7-KR6 对应的六个 snapshot schema 均存在：`realtime_map_snapshot`、`elevator_state_snapshot`、`route_replay_snapshot`、`labeling_queue_snapshot`、`voice_asr_tts_snapshot`、`safe_command_snapshot`。
- `board_media_preflight_summary` 作为 KR5 前置缺口 summary 仍存在，且保持 `safe_to_control=false`、`primary_actions_enabled=false`。
- 顶层 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`。
- `manual_control_policy` 与 `safe_command_snapshot` 的 `command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`。
- `voice_asr_tts_snapshot.tts_send_enabled=false`。
- `labeling_queue_snapshot.submit_enabled=false`。
- `route_replay_snapshot.playback_available=false`。
- 序列化后的 source response 不出现 `/cmd_vel`、USB/ACM 串口设备、ready-to-control 文案、`delivery_success=true`、`success_claim_allowed=true` 或 `pass=true` 类危险外推。

`acceptance_verdict=blocked_not_proven_guard_ok` 只表示上述 guard 条件仍保持，不表示真实 RTC/视频、ASR/TTS、地图、电梯、回放、标注、手控、寻路、robot ACK、cancel/stop/recovery 或底盘安全已经完成。

## Realtime Map Snapshot

`realtime_map_snapshot` 是 O7-KR1 的 fail-closed 字段契约。它让 PC Console 明确显示 map/pose 所需字段，但当前仍是 `software_proof` 和 `blocked_not_proven`，不能解释为真实 ROS2 `/tf`、真实地图、真实路线成员关系或刷新延迟小于 2 秒。

固定字段：

- `schema=trashbot.o7.realtime_map_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `map_ref.value=not_connected`
- `map_ref.status=not_proven`
- `map_frame.value=map`
- `map_frame.status=contract_placeholder_not_tf`
- `robot_pose.x_m/y_m/yaw_rad=null`
- `robot_pose.pose_source=not_connected`
- `pose_freshness.age_ms=null`
- `pose_freshness.latency_lt_2s_proven=false`
- `route_membership.on_route=false`
- `route_membership.in_elevator_zone=false`
- `route_membership.status=not_proven`

`blocked_reasons` 必须至少包含 cloud realtime API 仍是 draft、ROS2 `/tf` forwarding 未证明、map artifact 未连接、机器人位置延迟小于 2 秒未证明。`not_proven` 必须覆盖真实 `/tf`、真实地图 artifact、真实机器人位姿、真实 route membership、真实 elevator zone membership 和 `robot_position_latency_lt_2s`。

## Elevator State Snapshot

`elevator_state_snapshot` 是 O7-KR2 的 fail-closed 字段契约。它让 PC Console 显示电梯状态链、当前楼层证据、目标楼层确认和人工接管原因的槽位，但当前不证明真实电梯门状态、楼层识别、到达楼层、状态链回放或人工接管事实。

固定字段：

- `schema=trashbot.o7.elevator_state_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `state_chain[0].state=not_connected`
- `state_chain[0].status=not_proven`
- `current_state=not_connected`
- `current_floor_evidence.floor_label=not_connected`
- `current_floor_evidence.confidence=null`
- `current_floor_evidence.status=not_proven`
- `target_floor.floor_label=not_connected`
- `target_floor.confirmation_status=not_proven`
- `human_takeover.required=true`
- `human_takeover.reason=real_elevator_state_chain_not_proven`

`blocked_reasons` 必须至少包含 elevator event archive 未连接、真实电梯门状态未证明、楼层识别未证明、人工接管原因未从 task record 回填。`not_proven` 必须覆盖真实电梯状态链、真实当前楼层、真实目标楼层确认、真实电梯到达和真实人工接管原因。

## Route Replay Snapshot

`route_replay_snapshot` 是 O7-KR3 的 fail-closed 字段契约。它让 PC Console 明确显示历史路线回放需要的 task selector、selected task、trajectory、playback cursor、keyframe/evidence refs、state transitions gaps 和 next required evidence，但当前仍是 `software_proof` 和 `blocked_not_proven`，不能解释为真实历史任务列表、真实轨迹回放、真实关键帧截图、真实状态转移或 O6 云端归档已经完成。

固定字段：

- `schema=trashbot.o7.route_replay_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `playback_available=false`
- `real_archive_connected=false`
- `task_selector.source_contract=history.route_replay.v1`
- `task_selector.status=blocked_no_cloud_task_archive`
- `task_selector.available_task_count=0`
- `task_selector.selected_task_id=not_connected`
- `task_selector.task_list_ref=missing_o6_cloud_task_archive`
- `selected_task.task_id/robot_id/route_id=not_connected`
- `selected_task.started_at_ms/completed_at_ms=null`
- `selected_task.status=not_proven`
- `selected_task.evidence_ref=missing_selected_task_record`
- `trajectory.frame_count=0`
- `trajectory.sample_frames=[]`
- `trajectory.frame_schema=pending_cloud_trajectory_frame_v1`
- `trajectory.status=blocked_no_trajectory_api`
- `playback_cursor.frame_index/timestamp_ms=null`
- `playback_cursor.playing=false`
- `playback_cursor.speed=0`
- `playback_cursor.status=blocked_not_available`
- `keyframes.count=0`
- `keyframes.sample_refs=[]`
- `keyframes.status=blocked_no_keyframe_archive`
- `evidence_refs.task_archive=missing_o6_cloud_task_archive`
- `evidence_refs.trajectory_api=missing_trajectory_api`
- `evidence_refs.keyframe_archive=missing_keyframe_archive`
- `evidence_refs.state_transition_archive=missing_state_transition_archive`
- `state_transitions.count=0`
- `state_transitions.sample=[]`
- `state_transitions.status=blocked_no_state_transition_archive`

`state_transitions.gaps` 必须至少包含 cloud task archive 未连接、trajectory frame schema 未回填、keyframe evidence refs 未回填、state transition timeline 未回填。`blocked_reasons` 必须至少包含 O6 cloud task archive 未连接、history route replay API 仍是 draft、trajectory frames 不可用、keyframe evidence refs 不可用、state transitions 不可用。`not_proven` 必须覆盖真实历史任务列表、真实 selected task、真实轨迹帧、真实 playback cursor、真实 keyframe evidence refs、真实 state transition timeline 和 cloud archive query latency。

`next_required_evidence` 是后续 O6/O7 对接清单，不是 PC 已经查询云端的证据；至少包含 O6 cloud task archive query contract、历史任务列表 fixture、含 map frame 和 timestamp 的 trajectory frame schema、keyframe evidence ref archive sample、state transition timeline archive sample，以及 PC playback cursor 与 cloud frames 绑定且不触发机器人控制的证明。

## Labeling Queue Snapshot

`labeling_queue_snapshot` 是 O7-KR4 的 fail-closed 字段契约。它让 PC Console 明确显示 review queue、selected item、label schema、allowed label types、draft labels、submit/rollback audit、dataset export gaps 和 next required evidence，但当前仍是 `software_proof` 和 `blocked_not_proven`，不能解释为真实标注队列、真实截图/帧、真实提交、真实回滚、真实训练集导出或 O6 annotation API 已经完成。

固定字段：

- `schema=trashbot.o7.labeling_queue_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `submit_enabled=false`
- `rollback_enabled=false`
- `real_annotation_api_connected=false`
- `dataset_export_available=false`
- `review_queue.source_contract=labeling.review_queue.v1`
- `review_queue.status=blocked_no_annotation_api`
- `review_queue.available_item_count=0`
- `review_queue.assigned_operator=not_connected`
- `review_queue.queue_ref=missing_o6_annotation_review_queue`
- `selected_item.item_id/task_id/frame_id=not_connected`
- `selected_item.media_ref=missing_review_item_media_ref`
- `selected_item.evidence_ref=missing_selected_labeling_item_record`
- `selected_item.status=not_proven`
- `label_schema.schema_ref=missing_label_schema`
- `label_schema.version=not_connected`
- `label_schema.status=blocked_no_label_schema_api`
- `label_schema.required_fields=[]`
- `allowed_label_types[].status=contract_placeholder_not_api`
- `draft_labels.count=0`
- `draft_labels.items=[]`
- `draft_labels.status=blocked_no_selected_item`
- `draft_labels.autosave_available=false`
- `submit_audit.status=blocked_not_available`
- `submit_audit.endpoint=POST /api/o6/annotations (future, disabled)`
- `submit_audit.audit_ref=missing_submit_audit_log`
- `rollback_audit.status=blocked_not_available`
- `rollback_audit.endpoint=POST /api/o6/annotations/rollback (future, disabled)`
- `rollback_audit.audit_ref=missing_rollback_audit_log`
- `dataset_export.status=blocked_not_available`
- `dataset_export.export_ref=missing_training_dataset_export`
- `dataset_export.supported_formats=[]`

`dataset_export.gaps` 必须至少包含 O6 annotation API 未连接、accepted label schema 未证明、reviewed items 不可用、dataset manifest export 不可用和 training split policy 未定义。`blocked_reasons` 必须至少包含 O6 annotation API 未连接、labeling review queue API 仍是 draft、label schema 不可用、selected review item 不可用、submit audit 不可用、rollback audit 不可用和 training dataset export 不可用。`not_proven` 必须覆盖真实标注队列、真实 selected item、真实 frame/screenshot media、真实 label schema、真实 cloud allowed label types、真实 draft label autosave、真实 annotation submit、真实 annotation rollback 和真实 training dataset export。

`next_required_evidence` 是后续 O6/O7 对接清单，不是 PC 已经查询云端的证据；至少包含 O6 annotation review queue query contract、label schema fixture with allowed types、selected review item with media evidence ref、draft label payload schema、submit annotation audit log sample、rollback annotation audit log sample、dataset export manifest contract，以及 PC labeling panel 与 cloud API 绑定且不触发机器人控制的证明。

## Voice ASR/TTS Snapshot

`voice_asr_tts_snapshot` 是 O7-KR5 的 fail-closed 字段契约。它让 PC Console 明确显示 ASR stream status、latest partial/final transcript 槽位、TTS draft text、voice profile、speaker dispatch status、command ACK/audit、media preflight dependency 和 next required evidence，但当前仍是 `software_proof` 和 `blocked_not_proven`，不能解释为真实 ASR 输入流、真实 transcript、真实 TTS 播放、真实 speaker ACK、真实音频设备、真实 RTC 或云端 voice API 已完成。

固定字段：

- `schema=trashbot.o7.voice_asr_tts_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `asr_stream_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `media_preflight_dependency.required=true`
- `media_preflight_dependency.source_schema=trashbot.o7_board_media_preflight.v1`
- `media_preflight_dependency.status=blocked`
- `asr_stream.source_contract=voice.asr_tts_operator.v1`
- `asr_stream.status=blocked_no_voice_api`
- `asr_stream.connection_state=not_connected`
- `asr_stream.last_event_at_ms=null`
- `asr_stream.partial_slot.text=""`
- `asr_stream.partial_slot.status=empty_not_connected`
- `asr_stream.partial_slot.evidence_ref=missing_asr_partial_transcript_trace`
- `asr_stream.final_slot.text=""`
- `asr_stream.final_slot.status=empty_not_connected`
- `asr_stream.final_slot.evidence_ref=missing_asr_final_transcript_trace`
- `tts_draft.text=""`
- `tts_draft.status=draft_disabled`
- `tts_draft.max_chars=0`
- `tts_draft.language=zh-CN`
- `tts_draft.voice_profile=not_connected`
- `tts_draft.confirmation_required=true`
- `speaker_dispatch.status=blocked_not_available`
- `speaker_dispatch.endpoint=POST /api/o7/operator/voice/tts (future, disabled)`
- `speaker_dispatch.sends_to_robot=false`
- `speaker_dispatch.idempotency_key_required=true`
- `speaker_dispatch.timeout_ms=null`
- `command_ack_audit.ack_status=blocked_no_ack_contract`
- `command_ack_audit.last_command_id=not_connected`
- `command_ack_audit.audit_ref=missing_voice_command_audit_log`
- `command_ack_audit.speaker_ack_ref=missing_speaker_dispatch_ack`
- `command_ack_audit.failure_event_ref=missing_speaker_failure_event`

`blocked_reasons` 必须至少包含 voice API 未连接、ASR event stream 未连接、TTS command ACK contract pending、speaker dispatch ACK 未证明、board media preflight blocked 和真实 ASR/TTS runtime 未连接。`not_proven` 必须覆盖真实 voice API、真实 ASR stream、真实 ASR partial/final transcript、真实 TTS draft send、真实 TTS playback、真实 speaker dispatch ACK、真实音频设备、真实 RTC 和真实 ASR/TTS runtime。

`next_required_evidence` 是后续 O6/O7/板端联调清单，不是 PC 已经查询云端或播放音频的证据；至少包含 voice ASR/TTS cloud API contract、带 partial/final events 的 ASR stream connection trace、含 voice profile 的 TTS draft payload schema、TTS command ACK/audit log sample、speaker dispatch ACK 或 failure event sample、board media preflight audio input/output pass，以及无底盘运动的 RTC media smoke。

PC Console 展示该 snapshot 不等于真实语音监听、真实文本识别、真实 TTS 下发、真实 speaker ACK、真实音频设备、真实 RTC 或真实控制完成；UI 不得提供 TTS 输入框、发送按钮或绕过云端的本地音频访问。

## Safe Command Snapshot

`safe_command_snapshot` 是 O7-KR6 的 fail-closed 字段契约。它让 PC Console 明确显示手动转向、速度/转向限制、自动寻路目标、地图 goal slot、云端命令 endpoint、幂等键、确认策略、robot ACK、timeout/cancel/stop/recovery 缺口和 next required evidence，但当前仍是 `software_proof` 和 `blocked_not_proven`，不能解释为真实手控、真实速度控制、真实自动寻路、真实键盘操作、真实 ACK、真实 cancel/stop/recovery 或底盘安全已经完成。

固定字段：

- `schema=trashbot.o7.safe_command_snapshot.v1`
- `source=software_proof`
- `snapshot_status=blocked_not_proven`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `command_dispatch_enabled=false`
- `manual_control_enabled=false`
- `navigate_goal_enabled=false`
- `keyboard_control_enabled=false`
- `real_command_api_connected=false`
- `real_robot_ack_connected=false`
- `manual_turn_envelope.source_contract=operator.safe_command_preview.v1`
- `manual_turn_envelope.status=blocked_not_proven`
- `manual_turn_envelope.sends_to_robot=false`
- `manual_turn_envelope.accepted_input_slots` 必须包含 `keyboard_arrow_keys_disabled`
- `manual_turn_envelope.requested_direction=not_connected`
- `manual_turn_envelope.velocity_limited=true`
- `manual_turn_envelope.steering_limited=true`
- `manual_turn_envelope.evidence_ref=missing_manual_turn_command_envelope_trace`
- `velocity_limits.max_linear_mps/max_angular_radps=null`
- `velocity_limits.status=blocked_no_robot_hil_limits`
- `velocity_limits.hardware_verified=false`
- `steering_limits.max_steering_angle_rad/max_turn_rate_radps=null`
- `steering_limits.status=blocked_no_robot_hil_limits`
- `steering_limits.hardware_verified=false`
- `navigate_goal_envelope.status=blocked_not_proven`
- `navigate_goal_envelope.sends_to_robot=false`
- `navigate_goal_envelope.goal_source=map_click_disabled`
- `navigate_goal_envelope.requires_map_goal_slot=true`
- `navigate_goal_envelope.evidence_ref=missing_navigate_goal_command_envelope_trace`
- `map_goal_slot.map_frame=map`
- `map_goal_slot.x_m/y_m/yaw_rad=null`
- `map_goal_slot.status=empty_not_connected`
- `map_goal_slot.evidence_ref=missing_map_goal_selection_trace`
- `cloud_command_endpoint.manual_turn=POST /api/o7/operator/commands/manual-turn (future, disabled)`
- `cloud_command_endpoint.navigate_goal=POST /api/o7/operator/commands/navigate-goal (future, disabled)`
- `cloud_command_endpoint.status=future_disabled`
- `cloud_command_endpoint.sends_to_robot=false`
- `idempotency_key_requirement.required=true`
- `idempotency_key_requirement.header=Idempotency-Key`
- `idempotency_key_requirement.status=required_not_connected`
- `idempotency_key_requirement.replay_policy=reject_duplicate_future_contract`
- `confirmation_policy.manual_turn_requires_confirmation=true`
- `confirmation_policy.navigate_goal_requires_confirmation=true`
- `confirmation_policy.keyboard_control_requires_hold=true`
- `confirmation_policy.status=blocked_no_confirmation_ui`
- `robot_ack_status.ack_status=blocked_no_robot_ack_contract`
- `robot_ack_status.last_command_id=not_connected`
- `robot_ack_status.ack_ref=missing_robot_command_ack`
- `robot_ack_status.timeout_ms=null`
- `robot_ack_status.cancel_ack_ref=missing_robot_cancel_ack`
- `robot_ack_status.stop_ack_ref=missing_robot_stop_ack`
- `robot_ack_status.recovery_ref=missing_robot_recovery_event`
- `evidence_gaps.timeout=missing_command_timeout_policy_and_trace`
- `evidence_gaps.cancel=missing_cancel_command_ack_trace`
- `evidence_gaps.stop=missing_stop_command_ack_trace`
- `evidence_gaps.recovery=missing_robot_recovery_event_trace`

`blocked_reasons` 必须至少包含 safe command API 未连接、manual turn dispatch 关闭、navigate goal dispatch 关闭、keyboard control 关闭、速度/转向限制未 HIL 验证、robot ACK timeout/cancel/stop/recovery 未证明。`not_proven` 必须覆盖真实手控、真实速度控制、真实转向控制、真实键盘控制、真实自动寻路下发、真实云端 command API、真实 robot ACK、真实 timeout/cancel/stop/recovery 和真实底盘安全。

`next_required_evidence` 是后续 O5/O7/Robot/Hardware 联调清单，不是 PC 已经调用云端或小车的证据；至少包含 cloud safe command API contract with bearer auth、idempotency key replay rejection trace、manual turn payload schema with velocity and steering limits、navigate goal payload schema with map frame and goal slot、operator confirmation UI policy trace、robot command ACK timeout trace、cancel/stop/recovery ACK trace，以及 Hardware HIL 或受控现场安全证据。

PC Console 展示该 snapshot 不等于真实手动转向、真实速度控制、真实转向控制、真实键盘控制、真实自动寻路、真实 robot ACK、真实 cancel/stop/recovery 或真实底盘安全完成；UI 不得提供方向键按钮、键盘绑定、地图点击下发或绕过云端的本地 ROS2/Nav2/WAVE ROVER 控制入口。

## Board Media Preflight

`board_media_preflight_summary` 是 O7 Console 对板端 media preflight 缺口的只读展示。当前 PC API 使用静态 fail-closed summary，让 operator 能在 Console 中看到 KR5 之前必须补齐的 RTC、摄像头、音频、ASR/TTS 和上车 smoke 证据。

该 summary 必须保持：

- `schema=trashbot.o7_board_media_preflight.v1`
- `overall_state=blocked`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `device_probe_allowed=false`
- `device_probe_attempted=false`
- `software_proof_only=true`

`blocked_reasons` 至少表达 PC 尚未采集板端 media preflight、RTC signaling/STUN/TURN 未证明、摄像头视频源未证明、音频输入输出未证明、ASR/TTS runtime 未证明。

`not_proven` 至少覆盖 `real_rtc_session`、`real_camera_video_source`、`real_audio_capture`、`real_audio_playback`、`real_asr_stream`、`real_tts_playback`、`orange_pi_media_runtime`、`on_robot_media_smoke`。

`next_required_evidence` 必须指向下一步真实证据，包括 Orange Pi 摄像头枚举、音频输入输出枚举、RTC signaling/STUN/TURN trace、带时间戳 camera frame、ASR partial/final transcript、TTS playback trace、CPU encoding budget 和无底盘运动的 on-robot media smoke。

PC Console 展示该 summary 不等于真实 RTC、真实摄像头、真实音频、真实 ASR/TTS 或真实控制完成；它不能替代上车 smoke。

## KR Views

`kr_views` 必须包含六项：

| KR | Surface | Current status | Needed next contract |
| --- | --- | --- | --- |
| O7-KR1 实时地图与机器人位置 | Map/Pose panel | blocked/not_proven | `realtime.map_pose.v1`，含 map frame、pose、freshness timestamp |
| O7-KR2 电梯状态展示 | Elevator state panel | blocked/not_proven | `realtime.elevator_state.v1`，含状态链、楼层证据、接管原因 |
| O7-KR3 历史路线回放 | Route replay panel | draft/blocked | `history.route_replay.v1`，含任务列表、轨迹帧、状态转移 |
| O7-KR4 数据标注/打标界面 | Labeling queue panel | draft/blocked | `labeling.review_queue.v1`，含 label schema、提交、回滚和审计 |
| O7-KR5 ASR/TTS | Voice monitor panel | blocked/not_proven | `voice.asr_tts_operator.v1`，含 ASR 事件流、TTS draft ACK |
| O7-KR6 手控/寻路 | Safe command preview panel | blocked/not_proven | `operator.safe_command_preview.v1`，含幂等键、确认、ACK、超时、取消和恢复 |

状态枚举仅允许 `draft`、`blocked`、`not_proven`。不得出现 `ready`、`passed`、`success` 或等价真实成功状态。

## Command Preview Policy

`command_previews` 只允许展示未来 safe API envelope：

- `requires_confirmation=true`
- `sends_to_robot=false`
- `status=blocked_not_proven`
- `cloud_endpoint` 必须标注 `future, disabled`
- UI 不得渲染成可点击控制按钮或绑定键盘控制

未来若要开启真实手控、寻路或 TTS dispatch，必须先补齐：

- cloud bearer/auth、幂等键和审计日志
- robot-side ACK、timeout、cancel、stop/recovery evidence
- Hardware HIL 或受控现场安全证据
- 失败提示和可恢复路径

## Current Boundaries

本契约当前只推进 O7 的 UI/API 对齐，不证明：

- 真实实时地图或机器人位置延迟小于 2 秒
- 真实电梯状态链或楼层识别
- 真实历史任务列表、历史轨迹归档或逐帧回放
- 真实关键帧截图、真实 evidence refs 或真实状态转移时间线
- 真实标注队列、真实截图/帧、真实标注提交、真实回滚或训练集导出
- 真实 ASR/TTS runtime
- 真实手动转向、速度控制或自动寻路下发
- 真实送达、投放或硬件安全
