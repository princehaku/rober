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

`remote_cloud_relay.py` 现在还公开 `GET /api/o7/cloud-archive/tasks` 的 O7 cloud archive tasks 只读 contract。当前没有真实 archive store 时固定 `archive_status=blocked_not_proven`、空任务、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有控制/语音/标注危险字段 false。`workstation/` 通过 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 probe 状态、task count、selected/latest、inspector 状态、dangerous true fields、blocked/not_proven。该能力不是真实云 archive、真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路或真实控制链路。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 route replay player。operator 加载本地 archive fixture 后，可以用 `Previous frame`、`Next frame`、`Reset cursor` 和本地 range cursor 检查 `route_replay_inspector.sample_frames` 的 timestamp、pose、velocity、state 和 evidence ref。该 cursor 只改变浏览器内存，不调用 API、不写后端、不发送机器人命令；未加载 archive、无 selected task、无 sample frames、inspector blocked 或显式 `playback_available=false` 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实云历史路线回放、真实地图叠加、真实机器人运动或真实控制。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 labeling review panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `labeling_queue_inspector.sample_review_items`，可以用 `Previous item`、`Next item` 和 `Reset item` 只在浏览器内切换当前 item，查看 item/frame/media/evidence、current label sample、draft label sample、allowed label types 和 schema 摘要。该 cursor 不调用 API、不提交标注、不回滚、不写后端、不导出数据集、不发送机器人命令；未加载 archive、无 selected task、无 review items 或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave 或真实训练集导出。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 voice ASR/TTS monitor panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `voice_asr_tts_inspector.sample_asr_events`，可以用 `Previous ASR event`、`Next ASR event` 和 `Reset ASR cursor` 只在浏览器内切换当前 ASR event，查看 event type、timestamp、transcript、confidence、evidence ref、latest partial/final 对比和 `tts_draft.confirmation_required=true` 的只读 TTS 草稿摘要。该 cursor 不调用 API、不写后端、不连接真实 ASR stream、不发送 TTS、不播放音频、不调度喇叭；未加载 archive、无 selected task、ASR events 与 TTS draft 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 voice API、真实 ASR/TTS runtime、真实 TTS send/playback、speaker ACK、音频设备或 O7-KR5 完成。

`remote_cloud_relay.py` 同时公开 `GET /api/o7/realtime-elevator/snapshot` 的 O7 realtime/elevator 只读 contract。当前未接真实 ROS2 `/tf`、真实地图、实时流或电梯设备时固定 `realtime_status=blocked_not_proven`、`snapshot_status=blocked_not_proven`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`latency_lt_2s_proven=false`、`route_membership.on_route=false`、`route_membership.in_elevator_zone=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。`workstation/` 通过 `GET /api/o7/realtime-elevator-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 map/pose/elevator/floor/takeover 摘要、dangerous true fields、blocked/not_proven。该能力不是真实实时地图、真实电梯状态、真实楼层识别、真实人工接管或真实控制链路。

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
