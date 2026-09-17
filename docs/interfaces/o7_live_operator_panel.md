# O7 Live Operator Panel API

## 2026-09-17 控制与状态性能更新

- 首屏响应新增可选 `direct_upper_status`，与本面板消费同一次上位机 `/api/status` 结果；`/health` 与状态读取并行。聚合函数不保留跨请求缓存，固定安全字段沿用原契约。
- App 首次进入与手动刷新都消费该聚合响应。连续刷新点击合并在途请求；刷新期间保留控制台组件与已有 WebRTC peer。旧服务缺少扩展字段时，前端兼容补读 direct status。
- Stop 只合并自身重复点击，保持 operator confirmation。普通 manual/operator 的迟到响应不能覆盖较新的 Stop 回执；动作回执返回后按钮立即释放，只读状态更新在后台执行且不重写动作文案。
- `serial_busy` 显示“串口忙，请稍后重试”；`preempted=true` 显示动作被 Stop 中断。该信息不证明物理停车或运动闭环成功。
- 离线验收：`npm test -- --run` 运行真实 Vue DOM/假 fetch/假 WebRTC；`node scripts/control-status-performance-probe.mjs --output ../../sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-pc-performance.json` 输出结构计数。基线每轮两次远端 status，更新后每轮一次，状态刷新媒体卸载与 close 请求均为零。无 HIL/4G/物理停车时延或 CPU 降幅结论。

## Endpoint

`GET /api/o7/live-operator-panel`

返回 schema：`trashbot.o7.live_operator_panel.v1`。

该接口是 PC 首屏用户控制台的只读契约，用于展示上位机 SSH、camera LAN 入口、LiDAR/Radar 缺口和手控按钮的 locked 状态。它不 SSH、不读取硬件、不发送底盘命令、不打开串口。camera 的实时 `/health` 与 `/devices` 结果以 `GET /api/o7/local-webrtc-camera` 为准；浏览器首屏只读该状态，不自动发送同源 `POST /api/o7/local-webrtc-camera/offer`，避免已有 active peer 或并发页面触发 409 conflict。operator 点击“重新连接预览”后，前端才通过该同源 offer 代理到上位机 `http://192.168.1.11:8088/offer`，创建 recvonly WebRTC 预览。这只证明摄像头媒体链路，不证明任何底盘控制能力。

2026-06-03 现场联调确认：WAVE ROVER 当前可写运动控制口不是 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`，而是 Orange Pi 板载 UART `/dev/ttyS5`。CEO 在上位机执行以下命令后，底盘可响应前进：

```bash
stty -F /dev/ttyS5 115200 raw -echo -crtscts
printf '{"T":1,"L":0.08,"R":0.08}\n' > /dev/ttyS5
```

同轮安全补充：Codex 已向 `/dev/ttyS5` 发送 `{"T":1,"L":0,"R":0}` 停车命令。`/dev/ttyS5` 由此可以作为当前手动控制的实测写入口记录，但 PC UI 仍不得因为“写运动已通”自动解锁：`T=130` 反馈查询在 `/dev/ttyS5 @115200` 上没有读到任何串口行，`T=1001` 和 robot ACK 仍未证明。

2026-06-04 起，`http://127.0.0.1:5173/` 默认首屏继续保持普通用户可读的 `Rober 控制台`，并把雷达与地图拆成两个独立区块：

- 预览：显示 `上位机 8088 ready` / 等待服务、`/dev/video1`，首屏不自动创建 WebRTC peer；operator 点击“重新连接预览”后才在页面内展示 WebRTC 摄像头画面，同时保留打开摄像头页面按钮作为 fallback。
- 实时雷达 (`/scan`)：只展示从 `radar.scan_proof_latest` 派生的 `/scan` readiness。只有 `latest_scan_once_observed=true` 且 `latest_scan_hz_observed=true` 时，`realtime_radar.ready=true`；raw packet proof 不参与该状态灯。
- 实时图 (`SLAM/map`)：显示干净地图占位，并根据 `realtime_radar` 与 map/SLAM artifact 摘要显示 `waiting_for_radar` 或 `waiting_for_mapping`。首屏不得再出现组合标题 `雷达未接入 / 等待建图`。
- 操控：显示方向按钮、`Stop` 和速度滑块；按钮点击会通过 PC 同源
  `/api/o7/direct-upper/base/manual` 代理发起短 pulse 请求，并把后端返回的发送/失败、
  ACK/T=1001 状态和锁定原因展示给 operator。
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
- `lidar_radar.scan_proof_latest.latest_scan_once_observed` 与
  `lidar_radar.scan_proof_latest.latest_scan_hz_observed` 是实时雷达 ready 的唯一输入；
  `lidar_radar.scan_proof_latest.latest_raw_packet_once_observed` 只能作为诊断材料。
- `lidar_radar.raw_packet_proof_latest.endpoint="/api/radar/raw-packet-proof/latest"`，展示
  latest raw bytes、sync header、packet parse 和 point 统计摘要；缺失时必须兼容显示
  `not_loaded` / `n/a`。
- `lidar_radar.raw_packet_proof_latest.safe_to_control=false`、
  `sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、
  `hil_pass=false`，PC 首屏只消费 8787 摘要，不执行 collector、不启动 ROS2、不打开
  LiDAR 串口、不发送 `A5 60` 或底盘命令。
- `realtime_radar.title="实时雷达 (/scan)"`，`status` 为 `"ready"` 或 `"blocked"`。
  `ready=true` 只允许在 `scan_once_observed=true` 且 `scan_hz_observed=true` 时出现。
  `readiness_source="scan_proof_once_and_hz_only"`，
  `raw_packet_ignored_for_ready=true` 固定标明 raw packet 不能点亮雷达。
- `realtime_map.title="实时图 (SLAM/map)"`，`status` 为 `"ready"`、
  `"waiting_for_radar"` 或 `"waiting_for_mapping"`。没有 `/scan` once+hz 时必须是
  `waiting_for_radar`；有 `/scan` once+hz 但没有 map/SLAM artifact 时必须是
  `waiting_for_mapping`。
- `camera.base_url="http://192.168.1.11:8088/"`，`camera.health_status="not_listening_observed"` 是兼容既有 live 面板合同的静态字段；本轮实时 health/devices 以 `GET /api/o7/local-webrtc-camera` 返回为准。`camera.video_source="/dev/video1"`，`camera.offer_auto_post_enabled=false` 保持后端只读合同；前端浏览器在 camera ready 后仍必须等待 operator 点击“重新连接预览”，才可 POST 本机 `/api/o7/local-webrtc-camera/offer` 创建本地预览。`camera.lan_page_url` 指向同 LAN camera 页面。
- `control.visible_directions=["forward","back","left","right","stop"]`。
- `control.speed.default_value=0.2`，`min=0`，`max=0.5`，`step=0.05`，`unit="m/s"`。
- `control.command_dispatch_enabled=false`，`control.sends_commands=false`，`control.robot_ack_connected=false`。
- `control.base_boundary.observed_write_device="/dev/ttyS5"`，`baudrate=115200`，`vendor_command_id="T=1"`，`feedback_request_id="T=130"`，`required_feedback_id="T=1001"`，`t1001_feedback_status="not_observed_after_t130"`。
- `control.base_boundary.manual_control_status="fail_closed_display_only"`，`forbidden_endpoint="/api/base/manual"`，`post_base_manual_enabled=false`。
- 当前实测底盘写入口为 `/dev/ttyS5 @115200`，运动命令示例为 vendor `T=1` 左右轮速 JSON；`GET /api/o7/live-operator-panel`
  合同仍保持只读，不能在该 endpoint 内直接下发，也不能让浏览器 POST `/api/base/manual`。
  方向按钮若要发起现场 PC 点动，只能调用 PC 本机 direct-upper manual 代理
  `/api/o7/direct-upper/base/manual`，再由 PC 后端按 env 和 guardrail 转发。

## Blocked Reasons

当前固定 blocked reasons：

- `base_serial_identity_not_proven`
- `t1001_feedback_not_observed`
- `robot_ack_not_connected`

这些 blocker 表示当前只能展示按钮和速度 UI，不能开放真实控制。`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ttyACM0` 不能证明底盘身份，现场已确认它不是本轮控制口；`/dev/ttyS5` 已能写入 `T=1` 控制底盘，但 `T=1001` 反馈未观测，robot ACK 未接入。

同一现场事实的另一半是：`/dev/ttyACM0` 已按 LiDAR/STC 雷达口处理。雷达 ROS2 接入应走
`ros2_trashbot_hardware lidar_driver`，串口参数为 `/dev/ttyACM0 @150000`，启动字节为
`A5 60`，停止序列为 `A5 00 A5 65 A5 65`。PC 首屏必须分开显示“实时雷达
(`/scan`)”与“实时图 (`SLAM/map`)”：raw packet proof 只能进入诊断详情，不能让
`realtime_radar.ready=true`。上位机真实跑出 `/scan` once+hz 前，地图必须保持
`waiting_for_radar`。

## UI Behavior

`O7LiveOperatorPanel.vue` 在默认首屏展示：

- `Rober 控制台`
- `预览` / `实时雷达 (/scan)` / `实时图 (SLAM/map)` / `操控` / `状态`
- camera health 和 LAN page link
- 页面内 WebRTC 摄像头 `<video>`，ready 后保持空闲提示；只有点击“重新连接预览”才通过本机 API 连接远端 `/offer`
- 实时雷达区只显示 `/scan` once+hz readiness、scan proof artifact 摘要和 blocker；不能用 raw packet proof 点亮雷达状态灯。
- 实时图区显示 map/SLAM 等待状态：没有 `/scan` 时 `waiting_for_radar`，有 `/scan` 但没有 map/SLAM artifact 时 `waiting_for_mapping`。
- `前进` / `后退` / `左转` / `右转` / `Stop`
- `W/A/S/D` 键盘点动分别等价于 `前进/左转/后退/右转`，`Space` 和 `X` 等价于
  `Stop`；输入框、速度滑条、可编辑区域和 repeat keydown 不触发遥控。
- speed slider 和数值
- 控制锁定提示与可展开的工程详情
- `/dev/ttyS5 @ 115200`、`T=1001 not_observed_after_t130`、`manual control fail_closed_display_only` 作为底盘安全边界摘要
- `Raw packet proof` 只能放在 `诊断详情/工程材料` 中，展示
  artifact/freshness/age/proof status、bytes、sync、packets 和 points；该材料只证明
  raw packet proof 可见，不证明 ROS2 `/scan`、SLAM/map 或 HIL。
- `雷达 / 建图 / 定位` 区提供 `Refresh scan proof`、`Read scan latest`、`Read map proof latest`、`Localize reset` 等按钮级 workflow。按钮必须走 PC 同源 `/api/o7/direct-upper/*`，并在返回文案里展示 artifact status、hz、TF、fallback、canonical path、failure/blocker、fail-closed/safety 字段；浏览器不得直连 8787、ROS graph、`/cmd_vel` 或串口。

方向按钮点击不再固定写死“已拦截”。当前行为：

- `前进` / `后退` / `左转` / `右转` POST PC 同源 `/api/o7/direct-upper/base/manual`。
- `Stop`、`Space`、`X` 使用独立 `/api/o7/direct-upper/base/stop`，可在点动或 operator 请求尚未返回时发出。
- UI 请求体包含 `direction`、`speed` 和 `duration_ms`；`forward/back` 使用当前滑块
  speed 和 `250ms`，`left/right` 使用更明显的 turn pulse：`speed=0.08`、
  `duration_ms=350`。Stop 使用专用端点且不带点动时长。PC 后端仍会二次限幅到
  `<=0.08 m/s`、`1..350ms`，上位机 8787 也继续执行 guardrail 和自动停车。
- PC 本机 manual 代理使用独立 `5500ms` 超时，避免上位机 `/api/base/manual` 的运动
  pulse、自动停车、`T=130` 请求和 `T=1001` 读取窗口被 status 的 `1200ms` 短超时提前打断。
- 上位机 HTTP 2xx 且返回 JSON 时，UI 显示“已发送（仍锁定）”，并展示
  `ACK not observed`、`T=1001 not observed`、`blocked_reasons` 和 `safe_to_control=false`。
- 未配置 env、PC 后端 400/502、远端 `timeout`、坏 JSON 或 direct status 非 ready 时，UI 显示明确失败原因，不隐藏锁定状态。
- 浏览器不直连 8787、不 POST `/api/base/manual`、不发送 `/cmd_vel`、不构造 WAVE ROVER JSON、不调用 ROS2 action 或云端 command。
- 摄像头 offer 返回 HTTP 409 / peer conflict 时，UI 只显示“已有预览连接，关闭其他页面或稍后重试”的可读提示；该失败不影响方向按钮继续调用 direct-upper manual 代理。

工程 blocked reasons 仍允许放在 `详情` 与按钮返回文案中；但不得把 HTTP 200 文案写成
`ready to control`、HIL pass、robot ACK connected 或 delivery success。

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

渲染验收需确认页面包含 `Rober 控制台`、`预览`、`实时雷达 (/scan)`、
`实时图 (SLAM/map)`、`操控`、`状态`，首屏不出现组合标题
`雷达未接入 / 等待建图`，不出现 `External Probe Artifact`、
`Real Material Acceptance`、`ASR`、`TTS`、`cloud`，首屏只读 camera 状态且不自动
POST `/api/o7/local-webrtc-camera/offer`，点击“重新连接预览”后才创建预览；若 offer
409，需要显示 peer conflict 可读提示。点击 `前进` 显示用户可懂的控制锁提示，console 无 app error。
direct-upper 按钮级验收还需覆盖 `Refresh scan proof`、`Read scan latest`、
`Read map proof latest`、`Localize reset` 中至少两个关键入口，且页面可见
`safe_to_control=false`、`ACK not observed`、`T=1001 not observed`、hz/TF/fallback 或
canonical path/failure reason。推荐在 8788 服务启动后运行：

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm run o7:direct-upper-workflow
```

该脚本输出 `.workstation-runtime/o7-direct-upper-browser-workflow.json` 和截图，只能作为
`browser_workflow_button_level`，不得外推为 PC WASD、HIL、AMCL/Nav2 或 delivery success。

远端联调只允许只读确认 SSH、8088 camera health/devices 和 8787 API 监听状态。PC dev server 需要用 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/` 启动，然后通过 `GET /api/o7/local-webrtc-camera` 读取上位机 `/health` 与 `/devices`。除非底盘身份、T1001 feedback 和 robot ACK 都被证明，否则不得发送控制命令。
