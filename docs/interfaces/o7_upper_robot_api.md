# O7 Upper Robot API

## 目标

上位机统一 API 解决 PC 端分散连接问题。PC 只配置一个 base URL：

```text
http://192.168.1.11:8787
```

8787 统一承接 camera、radar、base 三类入口：

- camera：代理本机 8088 WebRTC camera smoke。
- radar：返回 `/dev/ttyACM0 @150000` 雷达设备、启动/停止字节和 ROS2 `/scan` 证明状态。
- base：返回 `/dev/ttyS5` 底盘写入口状态，并提供低速点动/停车 API。

## Vendor 来源

已采用本地资料：

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机为 UART JSON 一行一包。
  - Orange Pi 真实串口路径必须现场确认，不能沿用 Raspberry Pi 默认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `base_speed_ctrl()` 使用 `{"T":1,"L":...,"R":...}` 写左右轮速度。
  - vendor 参考 baudrate 为 `115200`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `T=1` 为底盘速度控制命令。
  - `T=130` 为底盘反馈请求，预期反馈应出现 `T=1001`。
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
  - ROS2/STC 参考 driver 打开串口 `150000`，启动时发送 `A5 60`，退出时发送 `A5 00 A5 65 A5 65`。
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
  - STC `idVendor=34bf`、`idProduct=ff0a` 可映射为 `/dev/lidar`；当前现场设备节点先按 `/dev/ttyACM0` 记录。

## 服务

脚本：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/upper_robot_api.sh`
- `onboard/scripts/install_upper_robot_api_service.sh`

systemd：

- `onboard/systemd/trashbot-upper-robot-api.service`
- unit name：`trashbot-upper-robot-api.service`
- 默认端口：`8787`
- 默认 camera 子服务：`http://127.0.0.1:8088`
- 默认 base 串口：`/dev/ttyS5 @115200`

安装：

```bash
cd /root/rober
bash onboard/scripts/install_upper_robot_api_service.sh --dry-run --repo-root /root/rober
bash onboard/scripts/install_upper_robot_api_service.sh --repo-root /root/rober
```

## Endpoints

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 统一 API 进程健康 |
| `GET` | `/api/status` | camera/radar/base 总览 |
| `GET` | `/api/camera/health` | 代理 8088 `/health` |
| `GET` | `/api/camera/devices` | 代理 8088 `/devices` |
| `POST` | `/api/camera/offer` | 代理 8088 `/offer`，只用于 recvonly WebRTC 视频 |
| `POST` | `/api/camera/peers/{peer_id}/close` | 代理 8088 peer cleanup |
| `GET` | `/api/radar/status` | 雷达设备和 `/scan` 证明状态 |
| `GET` | `/api/base/status` | `/dev/ttyS5`、pyserial、反馈/ACK 状态 |
| `POST` | `/api/base/stop` | 发送 `{"T":1,"L":0,"R":0}` 停车 |
| `POST` | `/api/base/feedback-request` | 发送一次非运动 `{"T":130}` 反馈请求并短窗口读取 JSON |
| `POST` | `/api/base/manual` | 低速方向点动，自动停车 |

## Base 控制安全边界

`/api/base/manual` 接收：

```json
{"direction":"forward","speed":0.08,"duration_ms":260}
```

规则：

- `direction` 只允许 `forward/back/left/right/stop`。
- `speed` 会被限制到 `ROBER_BASE_MAX_SPEED`，默认 `0.12`。
- `duration_ms` 会被限制到 `800ms` 以内。
- 每次方向命令后都会自动发送 `{"T":1,"L":0,"R":0}`。
- 响应会保留 `feedback_ack.t1001_observed=false` 和 `robot_ack_connected=false`，因为当前 `/dev/ttyS5` 上 `T=130` 还没有读到 `T=1001`。

因此，8787 只能声明“低速点动写入口可用”，不能声明“闭环安全控制完成”。

### 2026-06-03 硬件安全收口

本轮只收口 8787 API 的硬件/API 安全语义，不新增真实上车材料：

- `direction` 非 `forward/back/left/right/stop` 时返回结构化失败，不写串口，不应由 aiohttp 冒泡为 500。
- `speed` 强制取绝对值并限制到 `ROBER_BASE_MAX_SPEED`，默认 `0.12`；`duration_ms` 强制限制到 `800ms`。
- 每次 accepted manual pulse 都先写 vendor `{"T":1,"L":...,"R":...}\n`，短窗口后再写 `{"T":1,"L":0,"R":0}\n`。
- 响应保留 `command_result`、`stop_result`、`serial_write_failures`、`manual_command_executed`、`auto_stop_attempted`、`auto_stop_executed`。
- `/api/base/stop` 的 `robot_control_executed` 只跟随 stop JSON 写入结果；pyserial 缺失、串口打开失败或写失败时必须为 `false`。
- `feedback_ack.t1001_observed=false` 固定保留，因为当前 API 不读取 `T=1001`，也不能把 `T=1` 写入成功当成 ACK 或 HIL。
- `/api/base/feedback-request` 是非运动请求入口，只允许发送一次 vendor `{"T":130}` 并读取短窗口反馈；HTTP 200、写入成功或坏帧计数都不能外推为真实 ACK/HIL。

本轮单元测试只使用 fake pyserial/mock 串口，不打开真实 `/dev/ttyS5`，不 SSH，不发送真实 WAVE ROVER JSON、`cmd_vel` 或运动命令。

## Radar / LiDAR ROS2 接入

`/api/radar/status` 不打开雷达串口，只返回 PC 可消费的上位机事实和 ROS2 下一步命令。当前现场确认：

- 雷达设备：`/dev/ttyACM0`
- 波特率：`150000`
- 启动命令：`A5 60`
- 停止序列：`A5 00 A5 65 A5 65`
- ROS2 driver：`ros2_trashbot_hardware lidar_driver`
- 目标 topic：`/scan`
- 原始 packet topic：`/lidar/raw_packet`
- frame：`laser_frame`

上位机预检：

```bash
modprobe ch341
modprobe cp210x
modprobe ftdi_sio
modprobe pl2303
modprobe cdc_acm
ls -l /dev/ttyACM0 /dev/lidar 2>/dev/null || true
```

ROS2 启动入口：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  lidar_publish_raw_packets:=true
```

8787 返回 `scan_status="not_proven"` 是刻意保留的验收边界：只有后续采到
`ros2 topic echo --once /scan`、`ros2 topic hz /scan` 和
`ros2 topic echo --once /lidar/raw_packet` 后，才能把雷达状态从设备已识别提升为
`/scan` 连续输出已证明。

## PC 配置

PC 端优先读取：

```bash
ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787
```

如果该变量存在，PC 的 `GET /api/o7/local-webrtc-camera` 会通过统一 API 读取：

- `GET /api/camera/health`
- `GET /api/camera/devices`
- `POST /api/camera/offer`
- `POST /api/camera/peers/{peer_id}/close`

旧变量 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088` 仍保留为兼容 fallback。

PC workstation 还提供本机 direct upper API，详见 `docs/interfaces/o7_direct_upper_pc_api.md`：

- `GET /api/o7/direct-upper/status`
- `POST /api/o7/direct-upper/base/stop`
- `POST /api/o7/direct-upper/base/feedback-request`
- `POST /api/o7/direct-upper/base/manual`

该 direct mode 只用于 PC 本地开发/现场操作。它绕过 cloud relay 作为必需路径，但不改变生产 4G 云路线；PC 响应必须继续保留 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`，直到有同源 ACK/HIL 材料。

## 2026-06-03 实测结果

部署：

- `trashbot-upper-robot-api.service` installed and enabled。
- 远端 `0.0.0.0:8787` listening。
- 主进程：`python3 /root/rober/onboard/scripts/upper_robot_api.py ... --base-port /dev/ttyS5`。

统一状态：

- `GET http://192.168.1.11:8787/health` 返回 `status=ready`。
- `GET http://192.168.1.11:8787/api/status` 返回：
  - `camera.status=ready`
  - `radar.observed_lidar_port=/dev/ttyACM0`
  - `radar.baudrate=150000`
  - `radar.start_command_hex=a5 60`
  - `radar.scan_status=not_proven`
  - `base.port=/dev/ttyS5`
  - `base.write_control_available=true`
  - `base.feedback_ack.t1001_observed=false`
- Hardware worker 后续现场核对到 `POST http://192.168.1.11:8787/api/base/feedback-request` 当前返回 HTTP `405`，`Allow=OPTIONS`；因此文档中的 feedback-request 合同仍只能按本机软件转发和 fail-closed contract 看待，不能写成远端 endpoint 已部署可用、真实 `T=130 -> T=1001` 已闭环、ACK 或 HIL 通过。

PC 页面验证：

- `ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173`
- 浏览器打开 `http://127.0.0.1:5173/`
- console errors：0
- `<video>` 存在
- `videoWidth=640`
- `videoHeight=480`
- `readyState=4`
- `srcObject=true`
- 页面显示 `摄像头画面已连接`
- 截图：`/tmp/rober-upper-api-camera-preview.png`

远端 peer cleanup：

- `GET http://192.168.1.11:8088/health`
- `active_peer_connections=0`
- `active_peer_ids=[]`
- `last_closed_frames_read=631`

## O1 Safe Pulse Acceptance Runner

脚本：

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`

用途：

- 为 O1 现场短时点动验收生成一次性 JSON artifact。
- 默认只读 `GET /api/status`，汇总 camera/radar/base 状态、base `/dev/ttyS5`、`115200`、`T=1001`/ACK 边界和 fail-closed 安全字段。
- 只有同时传入 `--execute-motion --confirm-physical-clearance` 时才允许 POST `/api/base/manual`。
- 执行模式使用 runner 侧 `speed <= 0.08`、`duration_ms <= 350` 的更严格上限，再交给 8787 API 自身的低速/限时/auto-stop guardrail。
- 执行模式在 manual response 后会追加 POST `/api/base/stop`，记录独立 stop evidence。
- 执行模式在 manual + extra stop 后会自动再读一次 `GET /api/status`，记录 `post_status_request`、`post_status_summary` 和 `post_t1001_feedback_status`，避免只凭 manual HTTP 200 或 stop HTTP 200 判断 ACK。
- 输出 `acceptance_verdict` 作为机器可读收口字段，状态包括 `dry_run_only`、`blocked_before_motion`、`motion_posted_without_ack`、`motion_posted_with_t1001`；其中任一步失败都必须带 `failed_step` 并保持 fail-closed。
- runner 不打开串口、不绕过 8787 API、不发送 ROS `/cmd_vel`。

默认 dry-run：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --once-json
```

dry-run 或执行模式都可以附带 operator report：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --dry-run \
  --operator-report-json /safe/runtime/operator_report.json \
  --once-json
```

`--operator-report-json -` 可从 stdin 读取对象 JSON。runner 会归一化执行前安全字段 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`，以及执行后观察字段 `observed_motion`、`observed_stop`、`operator_notes`、`reported_at`，并输出 `operator_report_status=missing|ready_for_execution|ready_for_review|unsafe_or_incomplete`。preflight 三项为 true 时是 `ready_for_execution`，可通过执行前 operator report gate；preflight 为 true 且执行后观察字段完整时是 `ready_for_review`。该报告只作为人工 preflight/观察材料；dry-run 带完整或半完整报告仍不 POST `/api/base/manual`，也不会把 `safe_to_control` 或 `hil_pass` 改成 true。

现场有人看护且 CEO 明确授权真实短 pulse 后，才允许使用：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --base-url http://192.168.1.11:8787 \
  --execute-motion \
  --confirm-physical-clearance \
  --operator-report-json /safe/runtime/operator_report.json \
  --direction forward \
  --speed 0.05 \
  --duration-ms 250 \
  --once-json \
  --output /safe/runtime/o1-ttyS5-safe-pulse-acceptance.json
```

证据边界：

- 默认 dry-run：`api_status_dry_run_not_hil`
- 执行模式：`api_manual_short_pulse_with_extra_stop_not_hil`
- 执行模式缺失或不安全 preflight operator report：`acceptance_verdict.failed_step=operator_report_missing_or_incomplete`，不发送 manual POST。
- 没有 `T=1001` 或等价 ACK 前，`acceptance_verdict.status` 必须是 `motion_posted_without_ack` 或更保守状态，runner 输出必须保持 `safe_to_control=false`、`delivery_success=false`。
- 即使 `acceptance_verdict.status=motion_posted_with_t1001` 且 `operator_report_status=ready_for_execution` 或 `ready_for_review`，也只代表 8787 status/manual response 中出现 ACK 线索并携带人工材料；仍不是 HIL pass，不能替代同源 `feedback_T1001.log`、ROS `/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- 本轮未执行真实 `/api/base/manual`，未发送任何运动 POST。
