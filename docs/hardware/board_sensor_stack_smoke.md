# Board Sensor Stack Smoke

本文记录 2026-06-09 开始采用的实板传感器-only bringup 入口。目标是证明
LiDAR、相机、静态 TF 与 `/map` 的 ROS2 topic 链路可观测；不是运动验证，
也不是机械标定结论。

## 适用场景

- `upper_robot_api.py` 常驻占用 `/dev/ttyS5`，本轮不能关闭该进程。
- 需要同时观察 `/scan`、`/camera/image_raw`、`/tf_static`、`/map`。
- 不允许发布 `/cmd_vel`，也不把底盘运动结果当作本轮验收范围。

## Launch 参数

`ros2_trashbot_bringup/bringup.launch.py` 新增了以下显式参数：

- `base_enabled`：默认 `true`。现场 sensor-only smoke 传 `false`，跳过 `esp32_bridge`。
- `lidar_enabled`：默认 `false`。显式启用 `ros2_trashbot_hardware/lidar_driver`。
- `lidar_serial_port`：默认 `/dev/ttyACM0`。
- `lidar_serial_baudrate`：默认 `150000`。
- `lidar_frame_id`：默认 `laser_frame`。
- `lidar_scan_topic`：默认 `/scan`。
- `static_laser_tf_enabled`：默认 `false`。
- `base_frame_id` / `laser_tf_*`：仅用于 smoke-only 静态 TF 拓扑证明。

## 推荐命令

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

推荐的最小采样命令：

```bash
ros2 topic echo --once /scan
ros2 topic echo --once /camera/image_raw
ros2 topic echo --once /tf_static
```

## 风险边界

- `static_laser_tf_enabled` 发布的是 smoke/拓扑 TF，不是机械标定值。
- `lidar_serial_baudrate=150000` 来自 `root@192.168.1.11` 实板 `lidar_driver` smoke 结果，
  不是来自 WAVE ROVER 底盘 UART 文档。
- `camera_device:=/dev/video1` 是当前 Orange Pi Zero 3 实板 + DV20 USB 的观察结果，
  不应写死成所有板卡的默认值。
- 本入口只解决传感器证据采集，不解决 `/dev/ttyS5` 与底盘桥的串口独占。

## 2026-06-10 LiDAR Motion Delta Probe

`sprints/2026.06.10_03-10_lidar_motion_delta_probe/` 在真实上位机
`root@192.168.1.11:37878` 上启动最小 ROS2 stack：

- `lidar_driver`：`/dev/ttyACM0 @ 150000`，发布 `/scan`。
- `esp32_bridge`：`/dev/ttyS5 @ 115200`，`command_mode:=speed`，提供 `/trashbot/stop`。
- 未启动 camera、Nav2 或 autonomous navigation。

本轮发送一次 bounded `/cmd_vel` 脉冲：`linear.x=0.03`，实际窗口
`0.22162205299537163s`，随后 `/trashbot/stop` 成功。采集结果：

- `motion_commands_sent=true`
- `stop_confirmed=true`
- `safe_to_control=false`
- `delivery_success=false`
- `command_integration_odom_delta_m=0.00601554609`
- `physical_motion_lidar_delta_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`

失败定位：baseline/post `/scan` 有 896/1194 帧，但当前可比 profile 只有
`paired_bins=1`，`median_abs_diff_m=0.006499767303466797`，
`changed_bin_ratio=0.0`，低于保守阈值。因此本轮不能把 LiDAR delta 写成
真实物理运动佐证；`/odom` 仍只能按 command integration 处理，不是实测里程计。

结束后已补跑清场：本轮 `lidar_driver` / `esp32_bridge` 进程清理完成，
`trashbot-upper-robot-api.service` 恢复为 `active`，`/dev/ttyS5` 与 `/dev/ttyACM0`
无本轮 ROS 进程残留占用。详见
`sprints/2026.06.10_03-10_lidar_motion_delta_probe/artifacts/remote_capture/final_process_check_after_rerun.log`。

## 2026-06-10 LiDAR Scan Aggregation Harden

`sprints/2026.06.10_03-30_lidar_scan_aggregation_harden/` 修复 `/scan`
发布形态：`lidar_driver` 不再把单个窄角度 packet 直接当完整 LaserScan
发布，而是默认累积多个 parsed `LidarPoint` 后再发布。聚合触发条件：

- 后一个 packet 首角小于前一个 packet 首角，按厂商上位机参考的 start angle
  回绕视为一轮 LiDAR 数据完成。
- 未观察到回绕时，达到 `scan_aggregation_max_packets` 且已有至少
  `scan_aggregation_min_points` 个有效点后兜底发布，避免现场长时间没有
  `/scan`。

重要边界：

- 聚合帧只使用真实 packet 中解析出的距离点，不伪造 360 度，也不把未覆盖角度
  填成虚假距离。
- `angle_increment` 是当前聚合点集的平均角度步长；它提升 motion-delta
  对比的角度覆盖，但不等于机械标定、真实运动证明或实测里程计。
- no-motion smoke 只允许启动 LiDAR 并采样 `/scan` 指标，禁止发布 `/cmd_vel`。
  建议记录 `ranges_count`、`finite_count`、`angle_min/max` 和 `angle_span_deg`。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `base_config.use_lidar: false`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - LiDAR 参考路径使用 `/dev/ttyACM*`，并以 start angle 回绕作为一轮数据输出触发。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - USB camera 参考入口为 OpenCV `VideoCapture`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/hardware_device_probe.md`
  - `/dev/video1` 是 DV20 USB 图像节点，`/dev/ttyACM0` 单独运行 `lidar_driver` 可产出 `/scan`
