# pc-tools

`pc-tools` 是 rober 的 PC 侧工作站目录，当前主架构是 Node.js + Vue：

```text
pc-tools/workstation/
```

本目录不安装到 Orange Pi，不进入 onboard Docker/Humble 镜像，不访问真实硬件、ROS graph、Nav2 runtime、串口设备或云端生产链路。它只能证明 PC 本地软件入口、JSON fixture 索引和只读 route safe summary 能工作。

## 当前入口

- `workstation/`：Node API + Vue UI，是 PC Tools 的主入口。
- `evidence/fixtures/`：保留脱敏 JSON fixture，由 Node API 和 Node 测试读取。
- `route/`：保留 fixed-route 调试说明；实际读取能力在 `workstation/src/server/routeDebugLoader.ts`。
- `training/`、`labeling/`：保留占位目录和后续工作入口，不代表真实训练或标注流水线已接入。

## O7 Operator Console

`workstation/` 现在包含 O7 Operator Console tab。该 tab 只消费 `GET /api/o7/operator-console` 返回的 `trashbot.o7.operator_console.v1` 契约，展示 O7 六个 KR 的 draft/blocked/not_proven 状态：实时地图/机器人位置、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。

O7 cloud runtime 现在由 `python -m ros2_trashbot_cloud_relay.remote_cloud_relay` 暴露 `GET /api/o7/operator-console`；实际 HTTP handler 和 `build_o7_operator_console_contract()` 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`，`cloud-relay/` wrapper 只 re-export，避免部署入口和 runtime handler 漂移。PC 端保持 `operator_mode=observe_only`、`command_dispatch_enabled=false`、`sends_to_robot=false`，不直连小车、不发送真实控制、不声明真实实时流或成功。

`workstation/` 还包含 `GET /api/o7/cloud-operator-console-probe?baseUrl=<url>` 和 O7 Previews 内的 “Cloud operator console probe” 区域。probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 回环 base URL，由 PC Node 后端只读拉取远端 `/api/o7/operator-console` 并检查 schema 与危险 true 字段。它只是 local HTTP contract proof，不是公网云、4G、生产云、机器人在线或 O7 完成证明。

`remote_cloud_relay.py` 现在还公开 `GET /api/o7/cloud-archive/tasks` 的 O7 cloud archive tasks 只读 contract。当前没有真实 archive store 时固定 `archive_status=blocked_not_proven`、空任务、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有控制/语音/标注危险字段 false。relay runtime 可选通过 `TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.cloud_archive_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 task list、route replay sample、label/voice/command safe summaries；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 probe 状态、task count、selected/latest、inspector 状态、四条 inspector summary、dangerous true fields、blocked/not_proven。四条 summary 只压缩 KR3 route replay frame/sample 且固定 `playback_available=false`、KR4 labeling queue/schema 且固定 `submit_enabled=false`、KR5 ASR/TTS count/text length 且固定 `tts_send_enabled=false`、KR6 safe command envelope/ACK blocker 且固定 `command_dispatch_enabled=false` 和 `robot_control_executed=false`，不透传完整远端 JSON。该能力不是真实云 archive、真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路、机器人 ACK 或真实控制链路。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 route replay player。operator 加载本地 archive fixture 后，可以用 `Previous frame`、`Next frame`、`Reset cursor` 和本地 range cursor 检查 `route_replay_inspector.sample_frames` 的 timestamp、pose、velocity、state 和 evidence ref。该 cursor 只改变浏览器内存，不调用 API、不写后端、不发送机器人命令；未加载 archive、无 selected task、无 sample frames、inspector blocked 或显式 `playback_available=false` 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实云历史路线回放、真实地图叠加、真实机器人运动或真实控制。

同一区块还提供只读 `Route replay trajectory minimap`。它只读取 `route_replay_inspector.sample_frames` 中有效数值型 `x_m/y_m`，用固定 SVG viewBox 归一化轨迹并把当前 marker 绑定到本地 route replay cursor；少于 2 个有效点或当前帧坐标无效时显示 blocked/unknown，不画成可用地图或确定机器人位置。面板持续显示 `trajectory_points=<n>`、`map_frame=<...>`、`current_marker=<...>`、`safe_to_control=false`、`playback_available=false` 和 `robot_control_executed=false`，不接真实地图、不发送控制命令、不声明机器人已运动。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 labeling review panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `labeling_queue_inspector.sample_review_items`，可以用 `Previous item`、`Next item` 和 `Reset item` 只在浏览器内切换当前 item，查看 item/frame/media/evidence、current label sample、draft label sample、allowed label types 和 schema 摘要。该 cursor 不调用 API、不提交标注、不回滚、不写后端、不导出数据集、不发送机器人命令；未加载 archive、无 selected task、无 review items 或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave 或真实训练集导出。

同一区块还提供 `Local draft annotation editor`。operator 可以基于当前 review item 在浏览器内存中选择 allowed label type、填写 `0..1` confidence 和 note；前端只做本地校验并显示 `local_memory_draft_valid`、`blocked_invalid_confidence` 或 `blocked_label_type_not_allowed`。草稿按 `task_id:item_id` 隔离，`Reset draft` 只重置当前 item 的内存草稿。该 editor 固定 `submit_enabled=false`、`autosave_available=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`、`cloud_write_executed=false`，不调用 API、不写后端、不导出训练集，也不新增 Submit/Save/Export 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 voice ASR/TTS monitor panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `voice_asr_tts_inspector.sample_asr_events`，可以用 `Previous ASR event`、`Next ASR event` 和 `Reset ASR cursor` 只在浏览器内切换当前 ASR event，查看 event type、timestamp、transcript、confidence、evidence ref、latest partial/final 对比和 `tts_draft.confirmation_required=true` 的只读 TTS 草稿摘要。该 cursor 不调用 API、不写后端、不连接真实 ASR stream、不发送 TTS、不播放音频、不调度喇叭；未加载 archive、无 selected task、ASR events 与 TTS draft 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 voice API、真实 ASR/TTS runtime、真实 TTS send/playback、speaker ACK、音频设备或 O7-KR5 完成。

同一区块还提供 `Local TTS draft editor`。operator 可以基于当前 `voice_asr_tts_inspector.tts_draft`、`voice_session` 和 latest partial/final 在浏览器内存中编辑 draft text、voice profile 和 language；前端只做本地校验并显示 `local_tts_draft_valid`、`blocked_tts_text_empty`、`blocked_tts_text_too_long`、`blocked_voice_profile_empty` 或 `blocked_language_empty`。archive 未加载、selected task 缺失、ASR/TTS 上下文缺失或 inspector blocked 时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地覆盖值。`Reset TTS draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`tts_send_enabled=false`、`playback_available=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`speaker_dispatch.sends_to_robot=false`、`cloud_write_executed=false`，不调用 API、不发送 TTS、不播放音频、不调度喇叭、不写云端，也不新增 Send/Speak/Play/Dispatch/Save/Submit 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 safe command review panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `safe_command_inspector.sample_commands`，可以用 `Previous command`、`Next command` 和 `Reset command cursor` 只在浏览器内切换当前 command，查看 command id/type/status、envelope、idempotency、evidence、manual/navigate envelope、confirmation policy、robot ACK blocker 和 evidence gaps。该 cursor 不调用 API、不写后端、不发送手控或寻路命令、不绑定键盘、不连接真实 command API；未加载 archive、无 selected task、command sample 与 manual/navigate envelope 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实手控、真实寻路下发、真实 robot ACK、真实 stop/cancel/recovery 或硬件安全。

同一区块还提供 `Local safe command draft editor`。operator 可以基于当前 `safe_command_inspector` 的 manual/navigate envelope、limits、map goal slot、idempotency 和 confirmation fixture 摘要，在浏览器内存中形成一条待确认手控或寻路草稿；前端只做本地校验并显示 `local_safe_command_draft_valid`、`blocked_manual_direction_not_allowed`、`blocked_invalid_navigate_goal` 或 `blocked_idempotency_key_missing`。archive 未加载、selected task 缺失、inspector blocked 或 manual/navigate 上下文不足时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地草稿。`Reset command draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`、`safe_to_control=false`、`cloud_write_executed=false`，不调用 API、不写云端、不发送手控或寻路、不绑定键盘，也不新增 Send/Run/Control/Navigate/Dispatch/Keyboard/Stop/Cancel/Recovery/Save/Submit 类入口。

`remote_cloud_relay.py` 同时公开 `GET /api/o7/realtime-elevator/snapshot` 的 O7 realtime/elevator 只读 contract。当前未接真实 ROS2 `/tf`、真实地图、实时流或电梯设备时固定 `realtime_status=blocked_not_proven`、`snapshot_status=blocked_not_proven`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`latency_lt_2s_proven=false`、`route_membership.on_route=false`、`route_membership.in_elevator_zone=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。relay runtime 可选通过 `TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.realtime_elevator_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 map/pose/elevator/floor/takeover safe summary；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/realtime-elevator-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 map/frame、`robot_pose_summary`、pose freshness、最多 5 条 `elevator_state_samples_summary`、floor/takeover 摘要、dangerous true fields、blocked/not_proven。O7 Previews 同时提供只读 `Realtime map pose preview` 和 `Elevator state timeline preview`：前者只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad` 并用固定 SVG viewBox 展示 fixture/probe pose marker，解析失败显示 `blocked_pose_coordinate_unavailable`；后者只展示最多 5 条状态链摘要，空样本显示 `blocked_not_proven`。`robot_pose_summary` 固定包含 `real_ros2_tf_connected=false`，状态链 sample 只展示 `state/status/timestamp_ms/evidence_ref` 白名单字段。该能力不是真实 RTC/视频、真实实时地图、真实 ROS2 `/tf`、真实电梯状态、真实楼层识别、真实人工接管、机器人 ACK 或真实控制链路。

`workstation/` 现在还包含 `GET /api/o7/previews/acceptance` 和 O7 Previews 顶部的 “O7 previews acceptance guard”。该 guard 只汇总已存在的本地/HTTP preview surface：cloud operator console probe、cloud archive tasks probe、realtime elevator probe、route replay player、Realtime map pose preview、Elevator state timeline preview、Route replay trajectory minimap、labeling review panel、Local draft annotation editor、voice monitor panel、Local TTS draft editor、safe command review panel、Local safe command draft editor。每个 surface 都明确 `evidence_boundary`、`blocked_reasons` 和 `not_proven`，仍是 software proof / `blocked_not_proven`。它固定 `reads_hardware=false`、`sends_commands=false`、`connects_cloud_production=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`robot_control_executed=false` 和 `real_*_connected=false`，不读取 fixture、不触发 probe、不发送命令、不连接生产云、不提升 O7 完成度。它明确当前仍没有真实 RTC/视频、真实手控/寻路、真实 robot ACK 或硬件 HIL 证据。

同一 guard 区块还显示 `O7 real capability gap summary`。该 summary 是前端从已加载 acceptance guard 响应派生的只读视图，按 O7-KR1~KR6 聚合现有 `surfaces`，展示 matched surface count、surface ids、blocked/not_proven 摘要、`remaining_real_capability_gaps` 和关键 false 字段 `safe_to_control=false`、`sends_commands=false`、`connects_cloud_production=false`、`robot_control_executed=false`。未加载 guard 时显示 `not_loaded`；它不新增 fetch、不读取 fixture、不触发 probe、不发送命令，也不把 O7 完成度从 software proof 提升为真实能力。

`workstation/` 现在还包含 `GET /api/o7/live-endpoints/manifest` 和 O7 Previews 内的 “O7 live endpoints manifest” 手动加载区。该 manifest 只读取环境变量，覆盖 O7-KR1..KR6 的未来真实 API 配置状态：`O7_RTC_REALTIME_URL` / `O7_RTC_REALTIME_TOKEN`、`O7_CLOUD_ARCHIVE_URL` / `O7_CLOUD_ARCHIVE_TOKEN`、`O7_ROUTE_REPLAY_URL` / `O7_ROUTE_REPLAY_TOKEN`、`O7_ANNOTATION_API_URL` / `O7_ANNOTATION_API_TOKEN`、`O7_VOICE_API_URL` / `O7_VOICE_API_TOKEN`、`O7_SAFE_COMMAND_API_URL` / `O7_SAFE_COMMAND_TOKEN`。URL 摘要只展示 `protocol://host/path`，不展示 query、hash、用户名或密码；token 只展示 `present` / `absent`。URL 含 credentials、query 或 hash 时 capability 标记为 `blocked`，`display_url=blocked_unsafe_url`，不会采用该 URL。页面默认不自动加载 manifest；operator 点击 `Load live endpoints manifest` 后只读取本机 PC 后端摘要，不执行 ping/connect/send/test command，不连接生产云，不读取硬件，不暴露 token。

manifest 顶层固定 `network_probe_executed=false`、`sends_commands=false`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`reads_hardware=false`、`token_values_exposed=false`、`url_query_hash_credentials_exposed=false`。默认没有 env 时 6 个 capability 都是 `not_configured`、`proof_status=not_proven`，并用 `required_live_evidence` / `remaining_real_capability_gaps` 明确仍缺真实 RTC/视频、实时 pose、云归档、路线回放、标注提交、ASR/TTS、safe command API、robot ACK 和硬件安全证据。接口契约见 `docs/interfaces/o7_live_endpoints_manifest_api.md`。

## 旧 Python 移除状态

CEO 最新要求已将 `pc-tools` 下旧 Python 脚本、Python helper 和 Python 测试入口移除。`pc-tools` 不再保留 `.py` 作为产品入口、gate 入口或测试入口。

范围检查命令：

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

该命令应返回空结果。`node_modules` 内依赖包不属于本轮清理范围。

## 运行与验证

工作站验证只使用 Node/Vue gate：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
```

这些验证只能证明 PC 工作站软件链路，不证明真实机器人、真实硬件、真实手机、真实云链路或真实交付成功。

## Fail-Closed 边界

所有 API/UI 响应必须保持：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`

即使本地 JSON 读取成功，工作站也不得声明真实 Nav2/fixed-route runtime pass、真实 HIL、真实 WAVE ROVER feedback、真实手机验收、dropoff/cancel completion 或 delivery success。
