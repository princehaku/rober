# O7 Live Operator Panel API

## Endpoint

`GET /api/o7/live-operator-panel`

返回 schema：`trashbot.o7.live_operator_panel.v1`。

该接口是 PC 首屏用户控制台的只读契约，用于展示上位机 SSH、camera LAN 入口、LiDAR/Radar 缺口和手控按钮的 locked 状态。它不 SSH、不读取硬件、不发送底盘命令、不打开串口。camera 的实时 `/health` 与 `/devices` 结果以 `GET /api/o7/local-webrtc-camera` 为准；浏览器首屏可在确认 camera ready 后通过同源 `POST /api/o7/local-webrtc-camera/offer` 代理到上位机 `http://192.168.1.11:8088/offer`，创建 recvonly WebRTC 预览。这只证明摄像头媒体链路，不证明任何底盘控制能力。

2026-06-03 现场联调确认：WAVE ROVER 当前可写运动控制口不是 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`，而是 Orange Pi 板载 UART `/dev/ttyS5`。CEO 在上位机执行以下命令后，底盘可响应前进：

```bash
stty -F /dev/ttyS5 115200 raw -echo -crtscts
printf '{"T":1,"L":0.08,"R":0.08}\n' > /dev/ttyS5
```

同轮安全补充：Codex 已向 `/dev/ttyS5` 发送 `{"T":1,"L":0,"R":0}` 停车命令。`/dev/ttyS5` 由此可以作为当前手动控制的实测写入口记录，但 PC UI 仍不得因为“写运动已通”自动解锁：`T=130` 反馈查询在 `/dev/ttyS5 @115200` 上没有读到任何串口行，`T=1001` 和 robot ACK 仍未证明。

2026-06-03 起，`http://127.0.0.1:5173/` 默认首屏改为普通用户可读的 `Rober 控制台`，只保留四个区块：

- 预览：显示 `上位机 8088 ready` / 等待服务、`/dev/video1`，并在页面内直接展示 WebRTC 摄像头画面；同时保留打开摄像头页面按钮作为 fallback。
- 地图：显示干净地图占位，明确 `雷达未接入 / 等待建图`；不得伪造真实 LiDAR `/scan` 点云。
- 操控：显示方向按钮、`Stop` 和速度滑块；按钮点击只显示普通用户文案 `控制锁定：底盘串口/反馈/ACK 未确认`。
- 状态：显示在线、安全锁、摄像头、雷达、底盘状态灯，不在首屏暴露 proof/not_proven/contract 字段。

## Response Contract

顶层固定继承 fail-closed 字段：

- `source="software_proof"`
- `proof_status="not_proven"`
- `pc_only=true`
- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

主要字段：

- `ssh.host="192.168.1.11"`，`ssh.port=37878`，`ssh.reachable=true`，`ssh.workstation_api_8787_status="not_listening_observed"`。
- `lidar_radar.dev_lidar="missing"`，`lidar_radar.stc_by_id="unresolved"`，`lidar_radar.scan_status="not_proven"`，`lidar_radar.pointcloud_fabricated=false`。
- `lidar_radar.raw_packet_proof_latest.endpoint="/api/radar/raw-packet-proof/latest"`，展示
  latest raw bytes、sync header、packet parse 和 point 统计摘要；缺失时必须兼容显示
  `not_loaded` / `n/a`。
- `lidar_radar.raw_packet_proof_latest.safe_to_control=false`、
  `sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、
  `hil_pass=false`，PC 首屏只消费 8787 摘要，不执行 collector、不启动 ROS2、不打开
  LiDAR 串口、不发送 `A5 60` 或底盘命令。
- `camera.base_url="http://192.168.1.11:8088/"`，`camera.health_status="not_listening_observed"` 是兼容既有 live 面板合同的静态字段；本轮实时 health/devices 以 `GET /api/o7/local-webrtc-camera` 返回为准。`camera.video_source="/dev/video1"`，`camera.offer_auto_post_enabled=false` 保持后端只读合同；前端浏览器在 camera ready 后可主动 POST 本机 `/api/o7/local-webrtc-camera/offer` 创建本地预览。`camera.lan_page_url` 指向同 LAN camera 页面。
- `control.visible_directions=["forward","back","left","right","stop"]`。
- `control.speed.default_value=0.2`，`min=0`，`max=0.5`，`step=0.05`，`unit="m/s"`。
- `control.command_dispatch_enabled=false`，`control.sends_commands=false`，`control.robot_ack_connected=false`。
- `control.base_boundary.observed_write_device="/dev/ttyS5"`，`baudrate=115200`，`vendor_command_id="T=1"`，`feedback_request_id="T=130"`，`required_feedback_id="T=1001"`，`t1001_feedback_status="not_observed_after_t130"`。
- `control.base_boundary.manual_control_status="fail_closed_display_only"`，`forbidden_endpoint="/api/base/manual"`，`post_base_manual_enabled=false`。
- 当前实测底盘写入口为 `/dev/ttyS5 @115200`，运动命令示例为 vendor `T=1` 左右轮速 JSON；PC 合同仍保持只读，不能在该 endpoint 内直接下发，也不能 POST `/api/base/manual`。

## Blocked Reasons

当前固定 blocked reasons：

- `base_serial_identity_not_proven`
- `t1001_feedback_not_observed`
- `robot_ack_not_connected`

这些 blocker 表示当前只能展示按钮和速度 UI，不能开放真实控制。`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ttyACM0` 不能证明底盘身份，现场已确认它不是本轮控制口；`/dev/ttyS5` 已能写入 `T=1` 控制底盘，但 `T=1001` 反馈未观测，robot ACK 未接入。

同一现场事实的另一半是：`/dev/ttyACM0` 已按 LiDAR/STC 雷达口处理。雷达 ROS2 接入应走
`ros2_trashbot_hardware lidar_driver`，串口参数为 `/dev/ttyACM0 @150000`，启动字节为
`A5 60`，停止序列为 `A5 00 A5 65 A5 65`。PC 首屏地图仍显示“雷达未接入 / 等待建图”，直到
上位机真实跑出 `/scan` 和 `/lidar/raw_packet` 证据。

## UI Behavior

`O7LiveOperatorPanel.vue` 在默认首屏展示：

- `Rober 控制台`
- `预览` / `地图` / `操控` / `状态`
- camera health 和 LAN page link
- 页面内 WebRTC 摄像头 `<video>`，ready 后自动通过本机 API 连接远端 `/offer`
- `前进` / `后退` / `左转` / `右转` / `Stop`
- speed slider 和数值
- 控制锁定提示与可展开的工程详情
- `/dev/ttyS5 @ 115200`、`T=1001 not_observed_after_t130`、`manual control fail_closed_display_only` 作为底盘安全边界摘要
- `Raw packet proof` 紧凑状态，展示 artifact/freshness/age/proof status、bytes、sync、
  packets 和 points；该材料只证明 raw packet proof 可见，不证明 ROS2 `/scan` 或 HIL。

方向按钮点击只更新本地 locked 文案，不调用控制 API，不发送 `/cmd_vel`、WAVE ROVER JSON、ROS2 action、云端 command 或任何底盘运动命令。工程 blocked reasons 只允许放在 `详情` 内，不能作为普通用户主文案。

后续若要把 PC 按钮从 locked 切到真实可控，必须新增单独控制 API，而不是改这个只读接口。控制 API 的最低要求：

- 串口目标显式固定或配置为 `/dev/ttyS5 @115200`，并在日志中记录 vendor 来源：`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 与 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- 每次方向命令必须是短时点动，并带自动停车兜底，例如发送目标 `T=1` 后，在超时窗口内发送 `{"T":1,"L":0,"R":0}`。
- 默认速度使用低速起步，现场命令 `L=0.08,R=0.08` 已能让底盘响应；PC UI 的速度上限仍需另做现场标定。
- 在 `T=1001` feedback 或等价 robot ACK 没接入前，UI 只能标注为“人工现场可控”，不得宣称闭环安全控制已完成。

## Acceptance

本地验收：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

渲染验收需确认页面包含 `Rober 控制台`、`预览`、`地图`、`操控`、`状态`，首屏不出现 `External Probe Artifact`、`Real Material Acceptance`、`ASR`、`TTS`、`cloud`，点击 `前进` 显示用户可懂的控制锁提示，console 无 app error。

远端联调只允许只读确认 SSH、8088 camera health/devices 和 8787 API 监听状态。PC dev server 需要用 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/` 启动，然后通过 `GET /api/o7/local-webrtc-camera` 读取上位机 `/health` 与 `/devices`。除非底盘身份、T1001 feedback 和 robot ACK 都被证明，否则不得发送控制命令。
