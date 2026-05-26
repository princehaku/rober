# O7 RTC Realtime Foundation Tech Plan

## 1. 方案总览

本轮按跨 owner Epic 执行。先补 O7 RTC/实时调试基础契约，再让 PC 工作站展示这些契约。实现必须保持 fail-closed：所有动作是 draft 或 blocked，不触发真实视频推流、真实 TTS、真实底盘控制或 Nav2。

链路目标：

```text
Orange Pi / ROS2 board status
  -> cloud-relay signaling/status contract
  -> pc-tools/workstation O7 operator console
```

板端不是可选项。视频 RTC 需要至少一个 board-side media capability/status producer；云端需要信令或信令占位；PC 端只能消费云端 contract。

## 2. Vendor 和现有代码依据

- `docs/vendor/VENDOR_INDEX.md`：硬件资料入口，明确 Orange Pi Zero 3、WAVE ROVER、UART/JSON 和 vendor source of truth 顺序。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/app.py`：vendor Raspberry Pi 上位机参考包含 Flask、Socket.IO、`aiortc`、`/offer`、`/video_feed`、音频 route。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`：vendor audio/video 配置参考。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/audio_ctrl.py`：vendor TTS/音频播放参考。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/25 主程序架构介绍.ipynb`：vendor 说明其 app 包含 webRTC、web-socket、Flask、`base_camera.py`、`audio_ctrl.py`。
- `cloud-relay/README.md`：当前云端主要是 command/status/ack 和 phone-safe API，不是 RTC 信令已完成。
- `docs/product/pc_tools_workstation.md`：当前 PC 工作站只读、PC-only、not_proven，不直接控制。

## 3. 分工

### Task A - Hardware RTC Source Boundary

Owner: `robot-hardware-engineer`

允许改动：

- `docs/interfaces/o7_realtime_hardware_sources.md`

任务：

- 核查 vendor WebRTC、视频采集、音频/TTS、摄像头占用和 Orange Pi 边界。
- 输出 hardware facts：哪些来自 vendor Raspberry Pi app，哪些在项目 Orange Pi 尚未证明。
- 不改硬件配置、不改 vendor 文件。
- 不直接更新 `tech-done.md`，返回验证证据给主会话整合，避免并行写同一文件。

验收命令：

```bash
rg -n "aiortc|/offer|/video_feed|audio_ctrl|video_fps|Picamera2|cv2.VideoCapture" docs/vendor/waveshare_wave_rover/ugv_rpi
git diff --check -- docs/interfaces/o7_realtime_hardware_sources.md
```

### Task B - Board Realtime Status Contract

Owner: `robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_interfaces/**`
- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/src/ros2_trashbot_bringup/**`
- `docs/interfaces/o7_board_realtime_status.md`

任务：

- 新增或扩展一个 board-side safe realtime status summary helper，表达 RTC/video/asr/tts/nav-control readiness。
- 只输出 status/draft/blocked 字段，不启动真实 RTC、不控制底盘、不播放音频。
- 字段必须能被 cloud-relay/PC 端消费：`media_agent_state`、`video_source_state`、`asr_stream_state`、`tts_playback_state`、`manual_control_policy`、`nav_goal_policy`、`not_proven`。
- 不直接更新 `tech-done.md`，返回验证证据给主会话整合，避免并行写同一文件。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test -p '*operator*gateway*.py'
git diff --check -- onboard/src/ros2_trashbot_interfaces onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup docs/interfaces/o7_board_realtime_status.md
```

### Task C - Cloud + PC O7 Operator Console

Owner: `full-stack-software-engineer`

允许改动：

- `cloud-relay/**`
- `pc-tools/workstation/src/**`
- `pc-tools/workstation/test/**`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`

任务：

- 在 cloud-relay 定义 O7 realtime/operator safe API 或 export helper，表达 RTC signaling required / not connected / blocked by missing board agent。
- 在 PC workstation 新增 O7 Operator Console tab，展示实时地图、电梯状态、历史回放、标注、ASR/TTS、手控/寻路六区。
- PC 端不直连机器人，不出现真实控制成功文案；所有按钮/输入都必须显示 draft/blocked/not_proven。
- 不直接更新 `tech-done.md`，返回验证证据给主会话整合，避免并行写同一文件。

验收命令：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
git diff --check -- cloud-relay pc-tools docs/product docs/interfaces sprints/2026.05.27_01-02_o7-rtc-realtime-foundation
```

## 4. 接口边界

推荐 schema 名称：

- `trashbot.o7_realtime_operator_console.v1`
- `trashbot.o7_realtime_operator_console_summary.v1`

必须字段：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only` 或 `cloud_contract_only`
- `cloud_contract_required=true`
- `board_media_agent_required=true`
- `rtc_signaling_state`
- `video_source_state`
- `asr_stream_state`
- `tts_command_state`
- `manual_control_state`
- `nav_goal_state`
- `not_proven`
- `next_required_evidence`

## 5. OKR 最低优先级核对

当前 `OKR.md` 4.1 节最低 Objective 是：

- O6：0%
- O7：0%

本 sprint 针对 O7。理由：CEO 明确指定 O7，并追问视频 RTC 是否需要板端协议打通；本轮修正 O7 实时能力基础，避免 PC 端空心 UI。O6 仍是 O7 的数据基础，但本轮只做 O7 所需的最小 cloud contract，不宣称 O6 完成。

## 6. 验收与收口

完成后必须更新：

- `tech-done.md`：各 owner 实际改动、验证结果、失败定位、剩余风险。
- `side2side_check.md`：对照 CEO 问题和 O7 KR 验收。
- `final.md`：是否允许 O7 从 0% 小幅上调；默认保持 0%，除非证据真实覆盖一个可复用子能力。

本轮不得因为 PC 页面存在就标记 O7 完成。RTC/视频、ASR/TTS、手控/寻路必须继续等待真实板端、云端和现场验证。
