# O1/O7 PC Manual HIL 与 LiDAR Start-Stop 隔离准入

## 目标

本文用于 Worker D 本轮低风险推进：不发真实串口命令、不 SSH 上车、不修改底盘控制代码，只把真实 PC 手控 HIL、LiDAR 一键 start/stop 和 operator report 的证据边界写清楚，供 Software、Full-stack 和现场操作员消费。

结论先行：

- WAVE ROVER 底盘控制口按当前现场材料使用 `/dev/ttyS5 @115200`，该口只允许走 WAVE ROVER UART newline-delimited JSON。
- LiDAR 按当前 ROS2/STC vendor 来源使用 `/dev/lidar` 或现场候选 `/dev/ttyACM0 @150000`，该口只允许发送 LiDAR start/stop bytes 并读取 `0xAA 0x55` packet 或 ROS2 `/scan`。
- PC 雷达 start/stop、scan proof、raw packet proof 不得打开、写入或复用 `/dev/ttyS5`。
- PC manual forward/back/left/right/stop 不得打开、写入或复用 `/dev/lidar`、`/dev/ttyACM0` 或 LiDAR by-id。
- `T=1001` 只作为 vendor feedback material；没有同场 command、stop、post-status、operator report 和安全观察时，不得写成 robot ACK、HIL pass 或 `safe_to_control=true`。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机链路是 UART、UTF-8、newline-delimited JSON；vendor Raspberry Pi reference 不是 Orange Pi 默认路径来源。
  - 当前 LiDAR source of truth 是 `docs/vendor/lidar_pkg_ros2-main/`，历史 `docs/vendor/lidar_ros/` 只作 ROS1/protocol 对比。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `BaseController` 使用 `serial.Serial(uart_dev_set, buad_set, timeout=1)`。
  - `process_commands()` 写入 `(json.dumps(data) + '\n').encode("utf-8")`。
  - `base_speed_ctrl()` 发送 `{"T":1,"L":input_left,"R":input_right}`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor speed 配置包含 `slow_speed: 0.2`、`max_speed: 1.3`，只能作为 vendor app reference；现场低速 pulse 仍需由本项目 HIL 参数显式控制。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_SPEED_CTRL=1`，`CMD_ROS_CTRL=13`，`CMD_BASE_FEEDBACK=130`，`CMD_BASE_FEEDBACK_FLOW=131`，`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/lidar_pkg_ros2-main/README.md`
  - ROS2 Humble 参考要求通过 `/dev/ttyUSB*` 或 `/dev/ttyACM*` 插拔确认雷达设备，并修改 `config/lidar_params.yaml`。
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
  - LiDAR baudrate 为 `150000`。
  - driver startup 写入 `A5 60`，shutdown 写入 `A5 00 A5 65 A5 65`。
  - packet sync header 为 `0xAA 0x55`，发布 `sensor_msgs/msg/LaserScan`。
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
  - vendor config 默认 `port_name: "/dev/lidar"`、`frame_id: "laser"`。
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
  - STC USB Serial `idVendor=34bf`、`idProduct=ff0a` 映射为 symlink `lidar`。

## 已证实的硬件结论

### WAVE ROVER 底盘 UART

- 采用资料来源：`base_ctrl.py`、`config.yaml`、`json_cmd.h` 和 `VENDOR_INDEX.md`。
- 传输形态：UART 串口，一行一个 JSON object，UTF-8 编码，以 `\n` 结束。
- vendor Raspberry Pi reference 是 `/dev/ttyAMA0 @115200`；本项目 Orange Pi 现场材料已把底盘控制口收敛到 `/dev/ttyS5 @115200`，不得回退到 `/dev/ttyAMA0` 或 `/dev/ttyACM0`。
- 运动命令：
  - `T=1`：左右轮速度命令，字段 `L/R`。
  - `T=13`：ROS velocity 命令，字段 `X/Z`，firmware comment 写 m/s 和 rad/s；真实底盘行为仍需 HIL 确认。
- 非运动反馈：
  - `T=130`：请求 base feedback。
  - `T=1001`：vendor base feedback，不能单独代表 robot ACK。
- HIL 前任何 API/status/proof 都必须固定 `safe_to_control=false`，除非现场证据包满足本文的 PC manual HIL 准入。

### LiDAR 串口

- 采用资料来源：`lidar_pkg_ros2-main/README.md`、`src/lidar_node.cpp`、`config/lidar_params.yaml`、`scripts/99-lidar.rules` 和 `VENDOR_INDEX.md`。
- 当前 stable 部署目标应优先使用 vendor udev symlink `/dev/lidar`；现场候选可使用 `/dev/ttyACM0 @150000`。
- LiDAR start bytes 是 `A5 60`，shutdown bytes 是 `A5 00 A5 65 A5 65`。
- LiDAR packet sync 是 `0xAA 0x55`；ROS2 proof 目标是 `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` TF。
- LiDAR proof 或 PC 雷达 start/stop 只证明传感器链路，不证明底盘可控、Nav2 可消费、SLAM 地图质量或 `safe_to_control=true`。

## 串口隔离规则

| 场景 | 允许端口 | 允许写入 | 禁止事项 | 证据边界 |
| --- | --- | --- | --- | --- |
| PC manual forward/back/left/right/stop | `/dev/ttyS5 @115200` | WAVE ROVER JSON，例如 `T=1` 和 stop | 不得打开或写入 `/dev/lidar`、`/dev/ttyACM0`、LiDAR by-id | `field_hil_material`，需 operator report |
| PC/base feedback request | `/dev/ttyS5 @115200` | 显式 `{"T":130}` | 不得发送 `T=1/T=13/T=131`，不得触碰 LiDAR | `vendor_feedback_material` |
| PC radar start | `/dev/lidar` 或 `/dev/ttyACM0 @150000` | LiDAR `A5 60` 或启动 ROS2 driver | 不得打开 `/dev/ttyS5`，不得发送 WAVE ROVER JSON | `lidar_runtime_material` |
| PC radar stop | `/dev/lidar` 或 `/dev/ttyACM0 @150000` | LiDAR `A5 00 A5 65 A5 65` 或停止 ROS2 driver | 不得打开 `/dev/ttyS5`，不得发送 WAVE ROVER JSON | `lidar_runtime_material` |
| LiDAR scan proof collector | 只读 ROS2 topic 或路径 metadata | 默认不写串口；raw collector 只写 LiDAR start/stop | 不得发送 `T=1/T=13/T=130/T=131` 或 `/cmd_vel` | `software_guard` 或 `lidar_runtime_material` |

## PC Manual HIL 准入

现场开始任何 forward/back/left/right/stop 前，必须满足：

1. 物理净空：机器人周围无人员、线缆、桌脚和易碰撞物；低速短 pulse 有足够缓冲距离。
2. 人工看护：操作员站在可立即断电或急停的位置；必须先知道如何物理停机。
3. 串口确认：本轮只能使用 `/dev/ttyS5 @115200` 作为底盘口；若 API 报告口径不是 `/dev/ttyS5`，本轮不得点动。
4. stop 先行：先执行一次 stop，并记录 stop response；stop 失败时禁止后续运动。
5. 低速短 pulse：初始 `speed <= 0.08`、`duration_ms <= 350`；每次只测一个方向。
6. 自动停车：manual API 必须在 pulse 后补发 stop；若 stop response 或 post-status 缺失，证据包不得标记为 HIL pass。
7. 同一 evidence ref：manual response、stop response、post-status、`T=1001`、operator report 和现场记录必须使用同一 `evidence_ref`。

## Operator Report 最小字段

PC/upper API 或人工报告至少记录：

```json
{
  "schema": "trashbot.o1.pc_manual_hil_operator_report.v1",
  "evidence_ref": "field-YYYYMMDD-HHMM-direction",
  "operator": "name-or-role",
  "site": "indoor-open-area",
  "base_port": "/dev/ttyS5",
  "base_baudrate": 115200,
  "lidar_port": "/dev/ttyACM0 or /dev/lidar",
  "lidar_baudrate": 150000,
  "direction": "forward|back|left|right|stop",
  "speed": 0.08,
  "duration_ms": 350,
  "pre_stop_ok": true,
  "manual_response_ok": true,
  "auto_stop_response_ok": true,
  "post_status_ok": true,
  "t1001_observed": true,
  "observed_motion": "short description",
  "physical_stop_ready": true,
  "near_miss_or_contact": false,
  "safe_to_control_candidate": false,
  "not_proven": [
    "ros_odom",
    "ros_imu",
    "ros_battery",
    "nav2_consumption",
    "delivery_success"
  ]
}
```

字段口径：

- `safe_to_control_candidate` 默认必须为 `false`；只有 Product/OKR Owner 收口 HIL 证据包后才能决定是否转正。
- `t1001_observed=true` 仍只是 vendor feedback material，不能覆盖 stop/operator 缺失。
- `lidar_port` 只用于记录现场传感器链路，不能被 manual HIL 逻辑打开或写入。

## 上位机 API 护栏

如果 Software 或 Full-stack 暴露 PC/operator API，应满足：

- `/api/base/manual`、`/api/base/stop`、`/api/base/status`、`/api/base/feedback-request` 只允许消费 WAVE ROVER base config，默认端口必须明确显示为 `/dev/ttyS5 @115200` 或 fail-closed。
- `/api/radar/start`、`/api/radar/stop`、`/api/radar/status`、scan proof/latest 只允许消费 LiDAR config，默认端口必须明确显示为 `/dev/lidar` 或 `/dev/ttyACM0 @150000`。
- status 页面必须同时展示 base port 和 lidar port，避免用户把 `/dev/ttyACM0` 当成底盘口。
- radar start/stop 返回体应固定包含 `sends_base_motion_commands=false`、`calls_base_manual=false`、`publishes_cmd_vel=false`。
- base manual 返回体应固定包含 `touches_lidar_serial=false`、`lidar_start_command_sent=false`、`lidar_stop_command_sent=false`。
- 没有 operator report 时，PC UI 可以展示 `manual_entry_available`，但不得展示 `field_hil_pass` 或 `safe_to_control=true`。

## 验收边界

本轮文档只完成 HIL 准入护栏，不产生 OKR 涨分，也不证明：

- PC WASD 已真实控车。
- LiDAR 一键 start/stop 已从 PC UI 完成。
- WAVE ROVER HIL pass。
- robot ACK。
- ROS `/odom`、`/imu/data`、`/battery` 真实可用。
- Nav2/SLAM 已消费 `/scan`。
- 电梯或送垃圾任务现场闭环。

下一步履约动作：

1. Full-stack/Software 在 PC/upper API 返回体中消费本文隔离字段，避免雷达 start/stop 触碰底盘口。
2. Hardware 在现场条件满足后按本文 operator report 字段采集低速短 pulse 材料。
3. Product/OKR Owner 只在证据包包含 command、stop、post-status、`T=1001`、operator report 和现场记录后，决定是否把 `safe_to_control_candidate` 转为正式 HIL 进展。
