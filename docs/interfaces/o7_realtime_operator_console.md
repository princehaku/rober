# O7 Realtime Operator Console Contract

## Scope

`trashbot.o7.operator_console.v1` 是 O7 PC 运营调试平台的最小 cloud-contract driven 契约。它用于让 `pc-tools/workstation` 先展示六个 KR 的界面骨架和阻塞原因，同时保持真实机器人链路关闭。

当前实现位置：

- cloud helper：`cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py::build_o7_operator_console_contract()`
- PC API：`GET /api/o7/operator-console`
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

PC 不直连机器人，不读取 ROS2 graph，不打开串口，不发送 WAVE ROVER、Nav2、TTS 或手控命令。

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
- 真实历史轨迹归档可回放
- 真实标注提交或训练集导出
- 真实 ASR/TTS runtime
- 真实手动转向、速度控制或自动寻路下发
- 真实送达、投放或硬件安全
