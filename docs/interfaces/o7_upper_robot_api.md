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
| `GET` | `/api/status` | camera/radar/base 总览；`base.feedback_samples_latest` 只读摘要 latest feedback samples artifact |
| `GET` | `/api/camera/health` | 代理 8088 `/health` |
| `GET` | `/api/camera/devices` | 代理 8088 `/devices` |
| `POST` | `/api/camera/offer` | 代理 8088 `/offer`，只用于 recvonly WebRTC 视频 |
| `POST` | `/api/camera/peers/{peer_id}/close` | 代理 8088 peer cleanup |
| `GET` | `/api/radar/status` | 雷达设备和 `/scan` 证明状态 |
| `GET` | `/api/radar/scan-proof/latest` | 只读回放最近一次 LiDAR `/scan` proof artifact；不启动 ROS2、不打开串口、不发送 `A5 60` |
| `GET` | `/api/radar/raw-packet-proof/latest` | 只读回放最近一次 LiDAR raw packet proof artifact；不执行 collector、不启动 ROS2、不打开串口、不发送 `A5 60` 或底盘命令 |
| `GET` | `/api/base/status` | `/dev/ttyS5`、pyserial、反馈/ACK 状态；只读摘要 latest feedback samples artifact |
| `POST` | `/api/base/stop` | 发送 `{"T":1,"L":0,"R":0}` 停车 |
| `POST` | `/api/base/feedback-request` | 发送一次非运动 `{"T":130}` 反馈请求并短窗口读取 JSON |
| `POST` | `/api/base/feedback-samples` | 重复发送非运动 `{"T":130}`，采集多样本 `T=1001` evidence |
| `GET` | `/api/base/feedback-samples/latest` | 只读回放最近一次 feedback samples JSON artifact；不打开串口、不发送命令 |
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
- 当方向写入和 auto-stop 写入都成功后，`/api/base/manual` 会在 stop 之后通过同一
  `base_port/base_baudrate` 发送一次 vendor `{"T":130}`，短窗口读取 `T=1001`，并把结果放入
  `feedback_ack`、`t1001_feedback_status` 和 `feedback_evidence`。
- `feedback_ack.robot_ack_connected`、`safe_to_control` 和 `hil_pass` 仍固定为 `false`。
  `T=1001` 只代表 vendor feedback material，不代表项目 robot ACK、HIL pass 或闭环安全控制。

因此，8787 只能声明“低速点动写入口可用”，不能声明“闭环安全控制完成”。

### Manual left/right vendor mapping

本轮按本地 vendor 资料复核 `/api/base/manual` 的 `left/right` 映射，没有发现 onboard 映射反向问题：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 的 `base_speed_ctrl(input_left, input_right)` 直接发送 `{"T":1,"L":input_left,"R":input_right}`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 在 `CMD_SPEED_CTRL` 下把 JSON `L/R` 传给 `setGoalSpeed(L,R)`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h` 注释写明 `A-left, B-right`，且 `setGoalSpeed()` 将左输入送入 `setpointA/leftCtrl()`、右输入送入 `setpointB/rightCtrl()`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/templates/control.js` 的官方 Web 控制同样使用纯左转 `L=-max_speed,R=+max_speed`、纯右转 `L=+max_speed,R=-max_speed`。

所以当前差速点动方向语义为：

| manual direction | vendor `T=1` wheel command | 含义 |
| --- | --- | --- |
| `forward` | `{"T":1,"L":+speed,"R":+speed}` | 左右轮同向前进 |
| `back` | `{"T":1,"L":-speed,"R":-speed}` | 左右轮同向后退 |
| `left` | `{"T":1,"L":-speed,"R":+speed}` | 左轮后退、右轮前进，原地左转 |
| `right` | `{"T":1,"L":+speed,"R":-speed}` | 左轮前进、右轮后退，原地右转 |
| `stop` | `{"T":1,"L":0,"R":0}` | 停车 |

`T=130/T=1001` 语义也按 vendor 边界处理：`json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`FEEDBACK_BASE_INFO=1001`；`uart_ctrl.h` 收到 `T=130` 后调用 `baseInfoFeedback()`；`ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`，字段包含 `L/R` 轮速、`r/p/y` IMU 姿态和 `v` 电源电压。它能作为 vendor feedback material，不能单独证明手控闭环、安全准入、ROS `/odom` 或 HIL pass。

如果现场反馈“左右转还不行”，优先按 `docs/hardware/o1_base_manual_turn_smoke.md` 做低速短 pulse 复核：净空、急停、左右轮物理方向、auto-stop 和 stop 后 `T=130 -> T=1001` 回读必须同场记录。

### 2026-06-03 硬件安全收口

本轮只收口 8787 API 的硬件/API 安全语义，不新增真实上车材料：

- `direction` 非 `forward/back/left/right/stop` 时返回结构化失败，不写串口，不应由 aiohttp 冒泡为 500。
- `speed` 强制取绝对值并限制到 `ROBER_BASE_MAX_SPEED`，默认 `0.12`；`duration_ms` 强制限制到 `800ms`。
- 每次 accepted manual pulse 都先写 vendor `{"T":1,"L":...,"R":...}\n`，短窗口后再写 `{"T":1,"L":0,"R":0}\n`。
- 响应保留 `command_result`、`stop_result`、`serial_write_failures`、`manual_command_executed`、`auto_stop_attempted`、`auto_stop_executed`。
- `/api/base/stop` 的 `robot_control_executed` 只跟随 stop JSON 写入结果；pyserial 缺失、串口打开失败或写失败时必须为 `false`。
- `/api/base/manual` 的反馈证据链严格排在 auto-stop 之后：方向 `T=1` 写入成功、停车 `T=1,L=0,R=0`
  写入成功后，才用同一串口配置发送 `T=130` 并短窗口读取 `T=1001`。
- 若方向写入或 stop 写入失败，`manual` 响应保留 `command_result`、`stop_result` 和
  `serial_write_failures`，`feedback_after_stop_attempted=false`，
  `t1001_feedback_status="skipped_due_to_manual_write_failure"`，不会把失败包装成成功。
- `manual` 响应里的 `feedback_ack.t1001_observed=true` 只说明 stop 后的显式 `T=130` 读取到了
  vendor `T=1001` 材料；`robot_ack_connected=false`、`safe_to_control=false`、`hil_pass=false`
  不变，不能把 `T=1` 写入成功或 `T=1001` 材料当成 ACK/HIL。
- `/api/base/feedback-request` 是非运动请求入口，只允许发送一次 vendor `{"T":130}` 并读取短窗口反馈；HTTP 200、写入成功或坏帧计数都不能外推为真实 ACK/HIL。
- `/api/base/feedback-samples` 是非运动多样本 evidence collector，只重复同一条 `T=130` 路径并聚合每个 sample 的 `T=1001` 观察状态；它不调用 `/api/base/manual`，不发送 `T=1/T=13/T=131` 或 `/cmd_vel`。
- `/api/base/feedback-samples/latest` 只读取 `ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH` / `--feedback-samples-artifact-path` 指向的 JSON artifact，默认 `runtime/base_feedback_samples_latest.json`；artifact 不存在或坏 JSON 时 fail-closed，不打开串口、不发送 `T=130` 或任何运动命令。
- `/api/base/status` 和统一 `/api/status` 的 `base.feedback_samples_latest` 只做 latest artifact `stat/read_text/json.loads` 摘要，默认 15 分钟新鲜度窗口；该 freshness 只是材料文件新鲜度，不是 HIL、ACK、`safe_to_control` 或可运动准入。

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

8787 返回 `scan_status="not_proven"` 是刻意保留的验收边界：只有后续分别采到
`ros2 topic echo --once /scan`、`ros2 topic hz /scan`、`ros2 topic echo --once /lidar/raw_packet`
和 `tf2_echo base_link laser_frame` 后，才能把雷达材料从设备已识别提升为 ROS2
runtime proof。PC 的“实时雷达 ready”只能认 `/scan` once + `/scan` hz；raw packet 与 TF 是
工程诊断/坐标链材料，不能单独替代 `/scan` ready。

### LiDAR scan proof artifact readback

`GET /api/radar/scan-proof/latest` 读取
`ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH` / `--lidar-scan-proof-artifact-path`
指向的 JSON，默认 `runtime/lidar_scan_proof_latest.json`。该 artifact 应由
`onboard/scripts/o1_lidar_scan_proof_collector.py` 生成。

readback 边界：

- 只做 `Path.read_text()` 和 `json.loads()`。
- artifact 缺失返回 `404`，坏 JSON 返回 `422`。
- 不启动 ROS2 LiDAR driver。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 `A5 60`、`T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- 固定 `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。

`o1_lidar_scan_proof_collector.py --expect-existing-topics` 仍然只读 ROS2 graph：

- 不启动 `ros2_trashbot_hardware lidar_driver`。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 LiDAR `A5 60` start bytes。
- 不发送 WAVE ROVER `T=1/T=13/T=130/T=131`，不发布 `/cmd_vel`。

collector artifact 的 `proof.required_observations` 必须独立包含四个 key：

| key | 证明对象 | ready 作用 |
| --- | --- | --- |
| `scan_once` | `ros2 topic echo --once /scan` | 证明 `/scan` 至少有一帧 LaserScan |
| `scan_hz` | `ros2 topic hz /scan` | 证明 `/scan` 有连续频率输出，可供 PC 判断实时雷达 |
| `raw_packet_once` | `ros2 topic echo --once /lidar/raw_packet` | 证明 driver 发布原始包，只作为工程诊断 |
| `tf` | `tf2_echo base_link laser_frame` | 证明 base 到 LiDAR frame 的 TF 链，只作为坐标链诊断 |

顶层 `proof` 同步保留机器可读摘要字段：

- `scan_once_observed`
- `scan_hz_observed`
- `scan_hz_average_rate_hz`
- `raw_packet_once_observed`
- `tf_observed`
- `all_required_observations_observed`

`o1_lidar_ros2_scan_smoke.sh` 是 LiDAR-only runtime smoke，允许启动 LiDAR driver 和静态 TF，
因此会在 driver 内发送 LiDAR `A5 60` start bytes；它必须拒绝 `/dev/ttyS5`，并继续固定
`safe_to_control=false`、`sends_base_motion_commands=false`、`calls_base_manual=false`、
`publishes_cmd_vel=false`。它的 `summary.json` 使用同一套 `required_observations`
四项字段，便于 PC 或人工脚本按 `/scan` once、`/scan` hz、raw packet once、TF 分开判读。

`GET /api/radar/status` 的 `scan_proof_latest` 暴露 latest proof artifact 的 compact
摘要，包括 `artifact.status`、`latest_proof_status`、`latest_scan_once_observed`、
`latest_scan_hz_observed`、`latest_scan_hz_average_rate_hz`、
`latest_raw_packet_once_observed`、`latest_tf_observed`、
`latest_all_required_observations_observed` 和 `latest_required_observations`。旧 artifact
缺少 hz/TF 字段时这些新增字段保持 `null`，不能把缺省解释成 observed。PC 主状态灯仍只认
`latest_scan_once_observed=true` 与 `latest_scan_hz_observed=true` 作为实时雷达 ready；
raw packet 与 TF 只作为工程诊断和坐标链 proof，不参与 ready 判定。该摘要只代表最近
artifact 的读取状态，不证明当前 ROS2 `/scan` 正在连续输出。

### LiDAR raw packet proof artifact readback

`GET /api/radar/raw-packet-proof/latest` 读取最近一次
`trashbot.o1.lidar_raw_packet_proof.v1` artifact。它的目标是把绕开 ROS2 runtime
blocker 的 raw bytes、`0xAA55` sync header、packet parse 和 point 统计材料回放给
PC/O7 operator。

raw packet proof 与 `/scan` proof 的边界：

- raw packet proof 可以证明 LiDAR 串口 raw bytes、sync header、packet parse 和 points
  material readiness。
- raw packet proof 不证明 ROS2 `LaserScan` 已发布，不证明 `/scan` hz，不证明 TF，不证明
  SLAM/Nav2 可消费。
- PC 的实时雷达状态不能把 `latest_raw_packet_once_observed=true` 或
  `latest_raw_bytes_observed=true` 当成 `/scan` ready。
- `/scan` proof 才是 PC 实时雷达的主判定来源，且应优先读取 `scan_once` 与 `scan_hz`
  两个字段。

readback 边界：

- 只做 artifact 读取、JSON 解析和摘要。
- 不执行 `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`。
- 不启动 ROS2 LiDAR driver。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 `A5 60`、停止序列、`T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- 固定 `sends_commands=false`、`sends_motion_commands=false`、
  `robot_control_executed=false`、`safe_to_control=false`、`hil_pass=false`。

`GET /api/radar/status` 与统一 `GET /api/status` 的
`radar.raw_packet_proof_latest` 摘要至少可包含：

- `endpoint="/api/radar/raw-packet-proof/latest"`
- `http_status`
- `artifact.status`
- `freshness.status`
- `artifact.age_ms` 或等价 age 字段
- `latest_proof_status`
- `latest_raw_bytes_observed`
- `latest_sync_header_observed`
- `latest_packet_parse_ok`
- `latest_points_observed`
- `latest_bytes_read`
- `latest_sync_header_count`
- `latest_packets_parse_ok`
- `latest_points_total`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `safe_to_control=false`
- `hil_pass=false`

PC workstation 只消费这些摘要字段并做兼容降级；字段缺失时显示
`not_loaded` / `unknown` / `n/a`，不得因为摘要缺失导致 UI 500。

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
- `2026.06.03_13-14_o1-8787-feedback-deploy` 已将当前 `onboard/scripts/upper_robot_api.py` 通过 `scp` 部署到远端 `/root/rober/onboard/scripts/upper_robot_api.py`，并重启 `trashbot-upper-robot-api.service`。部署后 `POST http://192.168.1.11:8787/api/base/feedback-request` 返回 HTTP `200`，`serial_open.ok=true`、`serial_write.command={"T":130}`、`serial_write.bytes_written=10`、`read_line_count=2`、`parsed_json_count=2`、`observed_feedback_types=[130,1001]`、`t1001_feedback_status=observed`。
- `2026.06.03_14-15_o1-8787-feedback-samples` 已将新增 `/api/base/feedback-samples` 的 `onboard/scripts/upper_robot_api.py` 部署到远端并重启 `trashbot-upper-robot-api.service`。部署后 `POST http://127.0.0.1:8787/api/base/feedback-samples` 返回 HTTP `200`，`schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`、`requested_sample_count=3`、`completed_sample_count=3`、`t1001_observed_count=3`、`observed_feedback_types=[130,1001]`、`all_samples_observed_t1001=true`、`partial_samples_observed_t1001=false`、`samples[].t1001_feedback_status=["observed","observed","observed"]`、`feedback_ack.t1001_observed=true`、`feedback_ack.robot_ack_connected=false`。
- 该验证只发送非运动 `T=130` feedback request；没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131` 或 ROS `/cmd_vel`。响应仍固定 `feedback_ack.robot_ack_connected=false`、`safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`，所以不能写成 robot ACK connected、HIL pass、闭环安全控制、真实 `/odom`、`/imu/data`、`/battery` 或 delivery success。

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
