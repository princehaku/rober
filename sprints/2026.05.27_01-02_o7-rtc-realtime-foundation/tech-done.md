# O7 RTC Realtime Foundation Tech Done

## sprint_type: epic

## 1. 实际改动

本轮回答 CEO 追问：“视频 RTC 不需要机器上协议打通吗？板子上的代码够了？”结论是：不够。已完成的真实进展是 O7 realtime foundation 的 board/cloud/PC 三段契约和 PC software proof，不是 RTC、ASR/TTS、手控或寻路实机打通。

### Task A - Hardware RTC Source Boundary

Owner: `robot-hardware-engineer`

实际改动：

- 新增 `docs/interfaces/o7_realtime_hardware_sources.md`。

验收事实：

- 已读取 `docs/vendor/VENDOR_INDEX.md` 和其指向的 Waveshare WAVE ROVER `ugv_rpi` 本地资料。
- vendor Raspberry Pi app 包含 `aiortc`、`/offer`、`/video_feed`、`audio_ctrl.py`、`Picamera2`、`cv2.VideoCapture(0)`、`config.yaml` 和 Raspberry Pi OS 相关配置参考。
- 这些资料只能证明 Raspberry Pi 上位机参考 app 有 WebRTC/视频/TTS/音频播放线索，不能证明 rober Orange Pi Zero 3、ROS2、cloud-relay、PC workstation、STUN/TURN、公网 HTTPS、真实摄像头或真实音频设备已经打通。

边界：

- 未改 `docs/vendor/**`。
- 未改硬件配置、串口参数、bringup 参数或 WAVE ROVER 固件。

### Task B - Board Realtime Status Contract

Owner: `robot-software-engineer`

实际改动：

- 新增 board-side O7 realtime status helper `operator_realtime_status.py`。
- `/api/status` 生产 `o7_board_realtime_status`。
- `/api/diagnostics` 生产 `o7_board_realtime_status` 和兼容别名 `board_realtime_status`。
- 新增 `docs/interfaces/o7_board_realtime_status.md`。

验收事实：

- contract 覆盖 `media_agent_state`、`video_source_state`、`asr_stream_state`、`tts_playback_state`、`manual_control_policy`、`nav_goal_policy`、`not_proven` 和 `next_required_evidence`。
- contract 固定保持 `software_proof_only=true`、`primary_actions_enabled=false`、manual/nav policy `enabled=false`、`safe_to_control=false`。
- 子 agent 报告验证通过：`Ran 394 tests ... OK`。

边界：

- 不启动真实 RTC。
- 不打开摄像头或麦克风。
- 不播放 TTS。
- 不发送 `/cmd_vel`、Nav2 goal 或 WAVE ROVER 控制。

### Task C - Cloud + PC O7 Operator Console

Owner: `full-stack-software-engineer`

实际改动：

- cloud-relay 新增 `build_o7_operator_console_contract()`。
- PC workstation 新增 `GET /api/o7/operator-console`。
- PC workstation 新增 `O7 Console` tab。
- 更新 `docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

验收事实：

- PC O7 Console 展示 O7 六个 KR：实时地图/机器人位置、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。
- 所有 KR 视图均为 `draft`、`blocked` 或 `not_proven`。
- contract 固定保持 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`operator_mode=observe_only`。
- 子 agent 报告 Node build/test/lint 通过，PC workstation tests 输出 `16 passed`。

边界：

- PC 不直连机器人。
- PC 不读取 ROS graph、串口或 Nav2 runtime。
- PC 不发送 TTS、手控、寻路或底盘命令。

## 2. 验证结果

工程子 agent 已报告：

- Hardware：vendor-source grep 和 scoped `git diff --check` 通过。
- Robot：focused tests 通过，关键输出 `Ran 394 tests ... OK`。
- Full-Stack：`npm run build`、`npm run test`、`npm run lint` 通过；PC tests 关键输出 `16 passed`。

Product closeout 验证：

- `rg -n "O7|Objective 7|PC 端运营调试|实时地图|ASR|TTS|手控|寻路" OKR.md sprints/2026.05.27_01-02_o7-rtc-realtime-foundation docs/interfaces/o7_* docs/product/pc_tools_workstation.md pc-tools/README.md`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.27_01-02_o7-rtc-realtime-foundation`

## 3. 偏差与范围控制

- `pre_start.md` 中默认不提升 O7 百分比；closeout 后产品判断允许从 0% 保守提升到约 5%，因为本轮确实形成可复用的 board/cloud/PC 契约和 PC 软件入口。
- 该提升只代表 O7 realtime foundation 的 contract/UI software proof，不代表六个 KR 任何一项真实 runtime 达成。
- O6 保持 0%，因为本轮没有完成云端数据存档、打标 API、模型推理接口或生产查询 API。

## 4. 剩余风险

- 真实 Orange Pi 摄像头、音频、TTS、CPU 编码、网络 NAT、STUN/TURN、HTTPS、鉴权和弱网恢复均未验证。
- vendor WAVE ROVER Raspberry Pi app 不能替代 rober Orange Pi + ROS2 + cloud + PC 验收。
- PC O7 Console 仍是 observe-only，不能作为真实 RTC viewer、真实 ASR/TTS 控制台或真实手控/寻路入口。
- 下一步需要 `robot-software-engineer` 主责补 board media agent 最小 smoke，`full-stack-software-engineer` 主责补 cloud signaling/status API，`rober-hardware-engineer` 主责补真实 Orange Pi 摄像头/音频枚举和资源证据。
