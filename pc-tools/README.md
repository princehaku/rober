# pc-tools

`pc-tools` 是 rober 的 PC 侧工作站目录，当前主架构是 Node.js + Vue：

```text
pc-tools/workstation/
```

本目录不安装到 Orange Pi，不进入 onboard Docker/Humble 镜像，不直接访问真实硬件、ROS graph、Nav2 runtime、串口设备或云端生产链路。当前 `workstation/` 已从纯只读 proof workstation 进入 **Robot API 控制台 V1**：可以通过 Node 代理读取上位机 Robot API 的 status/latest/readback 短摘要，并把 O6 consumer detail / Mock field evidence 作为 task_id 证据视图；危险动作仍全部 fail-closed。当前默认首屏已经切回 `Robot Control`，`Route Debug` 仍保留为入口但不再是普通用户的默认落点，`source=software_proof` / `proof_status=not_proven` 这类 proof flags 也下沉到 `Proof Boundary` 的高级安全信息里。

## 当前入口

- `workstation/`：Node API + Vue UI，是 PC Tools 的主入口。
- `evidence/fixtures/`：保留脱敏 JSON fixture，由 Node API 和 Node 测试读取。
- `route/`：保留 fixed-route 调试说明；实际读取能力在 `workstation/src/server/routeDebugLoader.ts`。
- `training/`、`labeling/`：保留占位目录和后续工作入口，不代表真实训练或标注流水线已接入。

## Robot Control Console V1

`workstation/` 新增 `Robot Control` tab 和 `GET /api/robot-control/summary?baseUrl=<robot-api-base-url>`。Vue 不直接跨域访问上位机；Robot API base URL 只交给 Node server 代理。代理只读取 `/api/status`、O3 proof latest、Camera/LiDAR/Base status/latest/readback 类 GET endpoint，并拒绝 unsafe URL、credentials、query/hash、非回环或非 RFC1918 局域网 host、schema drift 和危险 true 字段。为避免真实上位机慢一点的状态聚合被误判成离线，`/api/status`、`/api/camera/health`、`/api/camera/devices` 采用更宽的只读超时窗口；其余 endpoint 继续保持短超时。当前 `Robot Control` 首屏已经回到普通用户可读的简易风格，只显示“小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航”五个区域和一个短地址输入，`task_id`、O6 base URL、Mock/field manifest、peer/ICE/SDP、readback table、O3 proof summary、route replay 和 evidence 细节都收进 `<details>` 折叠区。

页面至少展示 task_id selector、Robot API connection、O3 proof summary、route replay/Mock fallback summary、evidence/keyframe/labeling readiness、manual/nav safe command boundary、Camera/LiDAR/Base readback 七区块。`task_id` detail 通过既有 O6 consumer adapter 获取；本地 field manifest 只作为显式 Mock/field evidence fallback。

所有真实控制入口默认 locked/disabled：`/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start、keyboard control、map click goal。V1 固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，不发布 `/cmd_vel`，不调用 `/api/base/manual`。

Robot Control 现在还包含 `Camera Preview` 卡片，但首屏只显示“打开画面/关闭画面”和一句简单状态；`peer_id`、`ICE`、`SDP`、`cleanup` 和会话细节都收进 `<details>`。Vue 只通过 workstation Node 代理调用 `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`；浏览器不直接访问上位机 `/api/camera/offer` 或 `/api/camera/peers/{peer_id}/close`。代理继承既有 `baseUrl` 安全围栏：仅允许 HTTP、loopback/RFC1918、拒绝 credentials/query/hash，且只暴露 camera offer/close 两个固定路径。当前上位机真实 contract 返回的是顶层 `type/sdp/peer_id` answer，workstation proxy 同时兼容这一路径和设计稿中的嵌套 `answer` 形态。页面默认 `preview_status=idle_not_started`，只在用户显式点击 `打开画面` 后创建 `RTCPeerConnection`、以 `recvonly video` 协商远端视频；点击 `关闭画面`、切换 `baseUrl`、重复打开或组件卸载时，都会先清理旧 peer。若打开失败，最终 `preview_status` 保留 `start_failed`，不会被 cleanup 覆盖成 `stopped_by_user`。即使图传成功，所有控制入口仍保持 disabled，`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 不变。

Robot Control 也已经接入 Radar/Map proof refresh V2。Vue 通过 workstation Node 固定 POST 代理调用 `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/map/proof/refresh?baseUrl=<robot-api-base-url>`，上位机 body 分别固定为 `{ timeout_s: 10, runtime_warmup_s: 6, start_runtime: true }` 与 `{ timeout_s: 45 }`。这两个动作只刷新 no-motion 证据窗，允许出现 `sends_commands=true`、`starts_ros2=true` 这类证据级 helper 行为，但首屏只显示“刷新雷达/刷新地图”、一个短状态和 `scan/tf` 或 `map/evidence` 的人话摘要；`latest_readback_key_values`、`non_motion_evidence_actions`、`hard_dangerous_true_fields`、`last refreshed time` 和 blocked reasons 都收进高级诊断区。它仍然不会打开 `/cmd_vel`、`/api/base/manual`、Radar start、Map start、Nav2 goal、keyboard control 或 map click goal；动作结束后会自动回刷 Robot Control summary。只有 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`command_dispatch_enabled=true`、`manual_control_enabled=true`、`navigate_goal_enabled=true`、`keyboard_control_enabled=true`、`sends_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`opens_base_uart=true`、`uses_base_uart=true`、`hil_pass=true` 等硬危险 true 字段才会 fail closed。

## O7 Operator Console

`workstation/` 现在包含 O7 Operator Console tab。该 tab 只消费 `GET /api/o7/operator-console` 返回的 `trashbot.o7.operator_console.v1` 契约，展示 O7 六个 KR 的 draft/blocked/not_proven 状态：实时地图/机器人位置、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。

O7 cloud runtime 现在由 `python -m ros2_trashbot_cloud_relay.remote_cloud_relay` 暴露 `GET /api/o7/operator-console`；实际 HTTP handler 和 `build_o7_operator_console_contract()` 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`，`cloud-relay/` wrapper 只 re-export，避免部署入口和 runtime handler 漂移。PC 端保持 `operator_mode=observe_only`、`command_dispatch_enabled=false`、`sends_to_robot=false`，不直连小车、不发送真实控制、不声明真实实时流或成功。

`workstation/` 还包含 `GET /api/o7/cloud-operator-console-probe?baseUrl=<url>` 和 O7 Previews 内的 “Cloud operator console probe” 区域。probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 回环 base URL，由 PC Node 后端只读拉取远端 `/api/o7/operator-console` 并检查 schema 与危险 true 字段。它只是 local HTTP contract proof，不是公网云、4G、生产云、机器人在线或 O7 完成证明。

O7 Previews 现在把 `O7 consumer read primary path` 作为历史回放和标注队列检查主入口。operator 先用 `Load consumer task list` 调用 PC 后端 `GET /api/o7/consumer-read/tasks?baseUrl=<loopback>`，再选择 task 并用 `Load consumer task detail` 调用 `GET /api/o7/consumer-read/tasks/<task_id>?baseUrl=<loopback>&fieldEvidenceManifestJson=<local-json>`；PC 后端固定请求 O6 `view=summary` 和 detail `include=trajectory,events,evidence,labeling,inference,tunnel`。若 O6 detail 已有合法 `trashbot.field_evidence_manifest.v1` 或 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`，PC adapter 优先使用远端 field evidence；只有远端缺失 field evidence 且本地 `fieldEvidenceManifestJson` 是合法 `trashbot.field_evidence_manifest.v1` 时，才用本地 manifest 补齐 `field_evidence`。本地 manifest 缺失、坏 JSON、顶层非 object、schema mismatch、unsafe copy 或 `safe_to_control=true` / `primary_actions_enabled=true` / `delivery_success=true` 等危险声明都会 fail closed。同一份 consumer detail 既驱动 route replay player，也驱动 `Consumer-detail labeling queue primary path`：前者只消费 `trajectory.sample_frames`、`events.sample_events`、`evidence.sample_evidence`、`labeling.sample_items`、`inference.sample_results` 和 `tunnel_status` 摘要，后者只读检查 `labeling/evidence/events/trajectory` 的白名单短摘要。两条主路径都支持本地 cursor / 只读浏览，但所有 cursor/playback 都只在浏览器内存中变化，不写后端、不重新下发机器人命令、不证明真实云 archive 或真实机器人运动；submit/export/rollback 继续关闭。缺 detail、unknown task、task id mismatch、轨迹缺失、blocked/not_proven/error/cancel 状态或危险 true 字段都会显示 `blocked_not_proven` / fail-closed reason；页面固定展示 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`、`robot_control_executed=false`。

O7 Previews 还新增了 `Field evidence consumer ingest` 主入口。它从 `trashbot.field_evidence_manifest.v1` 出发，把 `route replay` 和 `labeling` 两条只读 preview 绑成同一份 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1` 摘要，供本地/mock manifest、route replay fixture 和 labeling fixture 共享同一输出结构。该入口只接受本地文件路径，不会把 UI 直接升级成真实回放、真实标注提交或控制面；`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 始终关闭。manifest 缺失、schema 不匹配、unsafe copy、preview 缺文件或 SSH 不可达时都会 fail closed，并显式暴露 blocked reason 与 next required evidence。

`remote_cloud_relay.py` 现在还公开 `GET /api/o7/cloud-archive/tasks` 的 O7 cloud archive tasks 只读 contract。当前没有真实 archive store 时固定 `archive_status=blocked_not_proven`、空任务、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有控制/语音/标注危险字段 false。relay runtime 可选通过 `TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.cloud_archive_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 task list、route replay sample、label/voice/command safe summaries；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 probe 状态、task count、selected/latest、inspector 状态、四条 inspector summary、dangerous true fields、blocked/not_proven。四条 summary 只压缩 KR3 route replay frame/sample 且固定 `playback_available=false`、KR4 labeling queue/schema 且固定 `submit_enabled=false`、KR5 ASR/TTS count/text length 且固定 `tts_send_enabled=false`、KR6 safe command envelope/ACK blocker 且固定 `command_dispatch_enabled=false` 和 `robot_control_executed=false`，不透传完整远端 JSON。该能力不是真实云 archive、真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路、机器人 ACK 或真实控制链路。

O7 Previews 的 `Cloud Archive Tasks` 区块仍保留 PC-only 本地 route replay player 作为次路径 / debug fallback。operator 加载本地 archive fixture 后，可以用 `Previous frame`、`Next frame`、`Reset cursor` 和本地 range cursor 检查 `route_replay_inspector.sample_frames` 的 timestamp、pose、velocity、state 和 evidence ref。该 cursor 与 consumer-detail 主路径 cursor 隔离，只改变浏览器内存，不调用 API、不写后端、不发送机器人命令；未加载 archive、无 selected task、无 sample frames、inspector blocked 或显式 `playback_available=false` 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实云历史路线回放、真实地图叠加、真实机器人运动或真实控制。

同一区块还提供只读 `Route replay trajectory minimap`。它只读取 `route_replay_inspector.sample_frames` 中有效数值型 `x_m/y_m`，用固定 SVG viewBox 归一化轨迹并把当前 marker 绑定到本地 route replay cursor；少于 2 个有效点或当前帧坐标无效时显示 blocked/unknown，不画成可用地图或确定机器人位置。面板持续显示 `trajectory_points=<n>`、`map_frame=<...>`、`current_marker=<...>`、`safe_to_control=false`、`playback_available=false` 和 `robot_control_executed=false`，不接真实地图、不发送控制命令、不声明机器人已运动。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 labeling review panel 作为 debug fallback。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `labeling_queue_inspector.sample_review_items`，可以用 `Previous item`、`Next item` 和 `Reset item` 只在浏览器内切换当前 item，查看 item/frame/media/evidence、current label sample、draft label sample、allowed label types 和 schema 摘要。该 cursor 不调用 API、不提交标注、不回滚、不写后端、不导出数据集、不发送机器人命令；未加载 archive、无 selected task、无 review items 或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave 或真实训练集导出，而且与 consumer-detail labeling primary path 的 cursor/state 隔离。

同一区块还提供 `Local draft annotation editor`。operator 可以基于当前 review item 在浏览器内存中选择 allowed label type、填写 `0..1` confidence 和 note；前端只做本地校验并显示 `local_memory_draft_valid`、`blocked_invalid_confidence` 或 `blocked_label_type_not_allowed`。草稿按 `task_id:item_id` 隔离，`Reset draft` 只重置当前 item 的内存草稿。该 editor 固定 `submit_enabled=false`、`autosave_available=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`、`cloud_write_executed=false`，不调用 API、不写后端、不导出训练集，也不新增 Submit/Save/Export 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 voice ASR/TTS monitor panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `voice_asr_tts_inspector.sample_asr_events`，可以用 `Previous ASR event`、`Next ASR event` 和 `Reset ASR cursor` 只在浏览器内切换当前 ASR event，查看 event type、timestamp、transcript、confidence、evidence ref、latest partial/final 对比和 `tts_draft.confirmation_required=true` 的只读 TTS 草稿摘要。该 cursor 不调用 API、不写后端、不连接真实 ASR stream、不发送 TTS、不播放音频、不调度喇叭；未加载 archive、无 selected task、ASR events 与 TTS draft 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 voice API、真实 ASR/TTS runtime、真实 TTS send/playback、speaker ACK、音频设备或 O7-KR5 完成。

同一区块还提供 `Local TTS draft editor`。operator 可以基于当前 `voice_asr_tts_inspector.tts_draft`、`voice_session` 和 latest partial/final 在浏览器内存中编辑 draft text、voice profile 和 language；前端只做本地校验并显示 `local_tts_draft_valid`、`blocked_tts_text_empty`、`blocked_tts_text_too_long`、`blocked_voice_profile_empty` 或 `blocked_language_empty`。archive 未加载、selected task 缺失、ASR/TTS 上下文缺失或 inspector blocked 时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地覆盖值。`Reset TTS draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`tts_send_enabled=false`、`playback_available=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`speaker_dispatch.sends_to_robot=false`、`cloud_write_executed=false`，不调用 API、不发送 TTS、不播放音频、不调度喇叭、不写云端，也不新增 Send/Speak/Play/Dispatch/Save/Submit 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 safe command review panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `safe_command_inspector.sample_commands`，可以用 `Previous command`、`Next command` 和 `Reset command cursor` 只在浏览器内切换当前 command，查看 command id/type/status、envelope、idempotency、evidence、manual/navigate envelope、confirmation policy、robot ACK blocker 和 evidence gaps。该 cursor 不调用 API、不写后端、不发送手控或寻路命令、不绑定键盘、不连接真实 command API；未加载 archive、无 selected task、command sample 与 manual/navigate envelope 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实手控、真实寻路下发、真实 robot ACK、真实 stop/cancel/recovery 或硬件安全。

同一区块还提供 `Local safe command draft editor`。operator 可以基于当前 `safe_command_inspector` 的 manual/navigate envelope、limits、map goal slot、idempotency 和 confirmation fixture 摘要，在浏览器内存中形成一条待确认手控或寻路草稿；前端只做本地校验并显示 `local_safe_command_draft_valid`、`blocked_manual_direction_not_allowed`、`blocked_invalid_navigate_goal` 或 `blocked_idempotency_key_missing`。archive 未加载、selected task 缺失、inspector blocked 或 manual/navigate 上下文不足时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地草稿。`Reset command draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`、`safe_to_control=false`、`cloud_write_executed=false`，不调用 API、不写云端、不发送手控或寻路、不绑定键盘，也不新增 Send/Run/Control/Navigate/Dispatch/Keyboard/Stop/Cancel/Recovery/Save/Submit 类入口。

`remote_cloud_relay.py` 同时公开 `GET /api/o7/realtime-elevator/snapshot` 的 O7 realtime/elevator 只读 contract。当前未接真实 ROS2 `/tf`、真实地图、实时流或电梯设备时固定 `realtime_status=blocked_not_proven`、`snapshot_status=blocked_not_proven`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`latency_lt_2s_proven=false`、`route_membership.on_route=false`、`route_membership.in_elevator_zone=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。relay runtime 可选通过 `TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.realtime_elevator_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 map/pose/elevator/floor/takeover safe summary；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/realtime-elevator-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 map/frame、`robot_pose_summary`、pose freshness、最多 5 条 `elevator_state_samples_summary`、floor/takeover 摘要、dangerous true fields、blocked/not_proven。O7 Previews 同时提供只读 `Realtime map pose preview` 和 `Elevator state timeline preview`：前者只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad` 并用固定 SVG viewBox 展示 fixture/probe pose marker，解析失败显示 `blocked_pose_coordinate_unavailable`；后者只展示最多 5 条状态链摘要，空样本显示 `blocked_not_proven`。`robot_pose_summary` 固定包含 `real_ros2_tf_connected=false`，状态链 sample 只展示 `state/status/timestamp_ms/evidence_ref` 白名单字段。该能力不是真实 RTC/视频、真实实时地图、真实 ROS2 `/tf`、真实电梯状态、真实楼层识别、真实人工接管、机器人 ACK 或真实控制链路。

`workstation/` 现在还包含 `GET /api/o7/previews/acceptance` 和 O7 Previews 顶部的 “O7 previews acceptance guard”。该 guard 只汇总已存在的本地/HTTP preview surface：cloud operator console probe、cloud archive tasks probe、RTC signaling contract probe、realtime elevator probe、route replay player、Realtime map pose preview、Elevator state timeline preview、Route replay trajectory minimap、labeling review panel、Local draft annotation editor、voice monitor panel、Local TTS draft editor、safe command review panel、Local safe command draft editor。每个 surface 都明确 `evidence_boundary`、`blocked_reasons` 和 `not_proven`，仍是 software proof / `blocked_not_proven`。它固定 `reads_hardware=false`、`sends_commands=false`、`connects_cloud_production=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`robot_control_executed=false` 和 `real_*_connected=false`，不读取 fixture、不触发 probe、不发送命令、不连接生产云、不提升 O7 完成度。它明确当前仍没有真实 RTC signaling/WebRTC/video/media transport、真实手控/寻路、真实 robot ACK 或硬件 HIL 证据。

同一 guard 区块还显示 `O7 real capability gap summary`。该 summary 是前端从已加载 acceptance guard 响应派生的只读视图，按 O7-KR1~KR6 聚合现有 `surfaces`，展示 matched surface count、surface ids、blocked/not_proven 摘要、`remaining_real_capability_gaps` 和关键 false 字段 `safe_to_control=false`、`sends_commands=false`、`connects_cloud_production=false`、`robot_control_executed=false`。未加载 guard 时显示 `not_loaded`；它不新增 fetch、不读取 fixture、不触发 probe、不发送命令，也不把 O7 完成度从 software proof 提升为真实能力。

`workstation/` 现在还包含 `GET /api/o7/live-endpoints/manifest` 和 O7 Previews 内的 “O7 live endpoints manifest” 手动加载区。该 manifest 只读取环境变量，覆盖 O7-KR1..KR6 的未来真实 API 配置状态：`O7_RTC_REALTIME_URL` / `O7_RTC_REALTIME_TOKEN`、`O7_CLOUD_ARCHIVE_URL` / `O7_CLOUD_ARCHIVE_TOKEN`、`O7_ROUTE_REPLAY_URL` / `O7_ROUTE_REPLAY_TOKEN`、`O7_ANNOTATION_API_URL` / `O7_ANNOTATION_API_TOKEN`、`O7_VOICE_API_URL` / `O7_VOICE_API_TOKEN`、`O7_SAFE_COMMAND_API_URL` / `O7_SAFE_COMMAND_TOKEN`。URL 摘要只展示 `protocol://host/path`，不展示 query、hash、用户名或密码；token 只展示 `present` / `absent`。URL 含 credentials、query 或 hash 时 capability 标记为 `blocked`，`display_url=blocked_unsafe_url`，不会采用该 URL。页面默认不自动加载 manifest；operator 点击 `Load live endpoints manifest` 后只读取本机 PC 后端摘要，不执行 ping/connect/send/test command，不连接生产云，不读取硬件，不暴露 token。

manifest 顶层固定 `network_probe_executed=false`、`sends_commands=false`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`reads_hardware=false`、`token_values_exposed=false`、`url_query_hash_credentials_exposed=false`。默认没有 env 时 6 个 capability 都是 `not_configured`、`proof_status=not_proven`，并用 `required_live_evidence` / `remaining_real_capability_gaps` 明确仍缺真实 RTC/视频、实时 pose、云归档、路线回放、标注提交、ASR/TTS、safe command API、robot ACK 和硬件安全证据。接口契约见 `docs/interfaces/o7_live_endpoints_manifest_api.md`。

`workstation/` 现在新增 `GET /api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>` 和 O7 Previews 内的 “RTC signaling contract probe” 手动面板。该 probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 这类本机回环 relay，不接受 HTTPS、外网 host、credentials、query 或 hash；它只拉取远端 `/api/o7/rtc-signaling/contract` 并校验 schema `trashbot.o7.rtc_signaling_contract.v1`。UI 只展示 remote schema、contract status、核心 false fields、protocol surface keys、required evidence refs、blocked/not_proven 和 dangerous true fields，不透传 token/auth/URL/credential-bearing payload。该 probe 固定 `network_probe_executed=false`、`connects_cloud_production=false`、`sends_commands=false`、`reads_hardware=false`，只是 HTTP contract probe，不证明真实 WebRTC、视频、media transport、RTC signaling session、实时 pose stream 或 ROS2 `/tf`。

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
