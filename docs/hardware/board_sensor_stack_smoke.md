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

## 2026-06-10 LiDAR Motion Delta Retry

`sprints/2026.06.10_03-45_lidar_motion_delta_retry/` 在聚合 `/scan`
修复后重跑一次受控低速 motion-delta capture。安全边界：

- 远端 `root@192.168.1.11:37878`，workspace `/root/rober/onboard`。
- `lidar_driver`：`/dev/ttyACM0 @ 150000`。
- `esp32_bridge`：`/dev/ttyS5 @ 115200`，`command_mode:=speed`，
  `feedback_debug_log_path` 打开。
- 本轮临时停止 `trashbot-upper-robot-api.service` 避免串口竞争，结束后恢复 active。
- 运动前 `/trashbot/stop` 成功，baseline `/scan` 健康后才发送命令。

本轮发送一次 bounded `/cmd_vel` 脉冲：

- `motion_commands_sent=true`
- `linear.x=0.03`
- `angular.z=0`
- `actual_pulse_duration_s=0.23607158900995273`
- `post_stop.success=true`

聚合 `/scan` delta 结果：

- `scan_frames_baseline=25`
- `scan_frames_post=39`
- `paired_bins=361`
- `median_abs_diff_m=0.003999948501586914`
- `changed_bin_ratio=0.09418282548476455`
- `physical_motion_lidar_delta_proven=false`

底盘反馈：

- 拉回的 `wave_rover_feedback_debug.jsonl` 共 348 条 `T=1001` 记录。
- `wheel_feedback_lr_nonzero_proven=false`，`left_speed/right_speed` 未出现非零。
- `/odom` 位移约 `0.00749907216m`，仍只代表 ROS-side command integration。

结论：本轮证明在 stop 可用、极低速、短窗口条件下可以发送并停止一次
bounded 控制脉冲；但 LiDAR delta 与 WAVE ROVER wheel feedback 仍不能证明真实
physical motion。`safe_to_control=true` 只适用于同等 bounded smoke 条件，
不等于自主导航或送达闭环可发车。清场已补跑确认：
本轮 `lidar_driver` / `esp32_bridge` / probe 无残留，`/dev/ttyS5` 与
`/dev/ttyACM0` 无本轮 ROS 占用，`trashbot-upper-robot-api.service` 为 `active`。

## 2026-06-10 04:00 Camera Visibility Boundary

`sprints/2026.06.10_04-00_board_camera_visibility_probe/` 在真实上位机
`root@192.168.1.11:37878` 上复核 `/dev/video1` 可见性。本轮只触碰
camera/OpenCV/v4l2/ROS camera topic，未发布 `/cmd_vel`，未启动底盘控制。

已证明：

- `/dev/video1` 仍是 DV20 USB 的 `uvcvideo` capture 节点，OpenCV 可打开并读帧。
- `bringup.launch.py base_enabled:=false camera_enabled:=true` 未显式传 `camera_device`
  时，`camera_publisher` 使用默认 `/dev/video1` 并发布 `/camera/image_raw`。
- `/camera/image_raw` subscriber 收到 `640x480 bgr8` 图像。
- 清场后无 `camera_publisher` / `bringup.launch.py` 残留，`/dev/video1` 无占用；
  brightness/gain/backlight 等临时控制项已恢复。

未证明：

- `visible_content_proven=false`。OpenCV MJPG/YUYV、640x480/320x240 与 ROS topic 样本的
  `non_black_ratio=0.0`、`edge_count=0`，不能用于路线关键帧、视觉定位、障碍识别或远程可视验收。
- 本轮不构成运动、导航、里程计或送达闭环证据。

下一步必须现场人工确认镜头盖/保护膜/遮挡、朝向、补光、USB 口和相机本体。

## 2026-06-10 WAVE ROVER Min Actuation Probe

`sprints/2026.06.10_04-15_wave_rover_min_actuation_probe/` 在真实上位机
`root@192.168.1.11:37878` 上通过现有 ROS2 `esp32_bridge` + `/cmd_vel`
路径做最小起动阈值阶梯 probe。本轮未改产品代码、launch、LiDAR driver、camera
代码或 firmware。

采用资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- 当前 `wave_rover_protocol.py` / `bridge_config.py` / `esp32_bridge_node.py`

安全边界：

- `lidar_driver`：`/dev/ttyACM0 @ 150000`。
- `esp32_bridge`：`/dev/ttyS5 @ 115200`，`command_mode:=speed`，
  `feedback_debug_log_path` 打开。
- probe 窗口临时停止 `trashbot-upper-robot-api.service`，结束后恢复 `active`。
- 每步后立即零速并调用 `/trashbot/stop`；最终严格复查 `lsof /dev/ttyS5 /dev/ttyACM0`
  无输出，`esp32_bridge` / `lidar_driver` / probe 无残留。

阶梯结果：

| `linear.x` | expected `T=1 L/R` | publish window | paired_bins | median_abs_diff_m | changed_bin_ratio | wheel feedback nonzero | command integration odom delta |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 0.03 m/s | 0.023077 | 0.164106s | 719 | 0.008000 | 0.312935 | false | 0.004503m |
| 0.05 m/s | 0.038462 | 0.166476s | 716 | 0.006750 | 0.284916 | false | 0.004998m |
| 0.07 m/s | 0.053846 | 0.167155s | 719 | 0.007000 | 0.255911 | false | 0.006891m |
| 0.09 m/s | 0.069231 | 0.177252s | 720 | 0.007500 | 0.298611 | false | 0.017972m |

结论：

- `motion_commands_sent=true`
- `max_step_linear_x_mps_sent=0.09`
- `physical_motion_lidar_delta_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `min_actuation_step_proven=null`
- `safe_to_control=true`，仅代表本轮 bounded smoke 可停与清场成功，不代表自主发车。
- `delivery_success=false`

失败定位：`linear.x=0.03-0.09m/s`、每步 `<=0.18s` 的低速短脉冲仍无物理运动
证据或 wheel feedback 非零。下一步需要现场肉眼/外部视频、检查电机供电/急停/模式/
底盘是否架空；若仍无运动，再考虑人工在场的 vendor direct `T=1` 更高 PWM/速度受控 HIL。

## 2026-06-10 Field HIL Execution Pack

`docs/hardware/field_hil_execution_pack.md` 已把当前证据矩阵和下一轮现场 HIL
顺序收敛为可执行 gate。后续不要继续盲跑远程低速 probe；必须先由现场人员确认
镜头盖/保护膜/补光/相机朝向、电机供电、急停/遥控/模式、底盘落地或架空状态、
安全空间和外部视频记录条件。

只有 `/trashbot/stop`、UART、battery/feedback、LiDAR scan、camera 可见性或外部视频、
API service 管理和清场条件全部通过后，才允许继续受控运动。`visible_content_proven`、
`physical_motion_lidar_delta_proven`、`wheel_feedback_lr_nonzero_proven`、
`delivery_success` 的翻转条件以该 execution pack 为准。

## 2026-06-10 Field HIL Operator Report Template

`docs/hardware/field_hil_operator_report_template.md` 已补充 `/api/operator/report`
现场人工材料提交模板。该入口用于记录 operator report、外部视频引用、相机可见性、
wheel feedback、scan delta、route/map 和 delivery 布尔值，但返回边界必须保持
`operator_report_material_only=true`。report 不能替代 `/trashbot/stop`、robot ACK、
`T=1001` feedback、HIL pass 或 motion proof。

## 2026-06-10 05:00 Live Sensor/API Snapshot

`sprints/2026.06.10_05-00_live_sensor_api_snapshot/` 在真实上位机
`root@192.168.1.11:37878` 上做了一次 no motion command 的 live sensor/API
snapshot。本轮只读 SSH、systemd、HTTP GET/readback、设备枚举、camera frame、
ROS topic 和已有 map/route artifacts；未发布非零 `/cmd_vel`，未发送 direct UART
`T=1`/`T=13`，未调用 `/api/base/manual`、`/api/radar/start`、`/api/map/start`、
`/api/nav2/start` 或任何会导致运动的 endpoint。`/api/base/status` 也被跳过，因为
当前实现会向 `/dev/ttyS5` 发送非运动 `T=130` feedback readback，本轮选择完全避免
UART 写入。

当前事实边界：

- SSH 可达，`trashbot-upper-robot-api.service` 为 `active (running)`。
- `/api/operator/report` readback 返回 missing latest artifact，但 guard 字段保持
  `operator_report_material_only=true`、`sends_motion_commands=false`、
  `safe_to_control=false`、`delivery_success=false`。
- `/dev/video0`、`/dev/video1`、`/dev/video2`、`/dev/ttyS5`、`/dev/ttyACM0`
  当前存在；`/dev/video1` 仍是 DV20 USB capture 候选，`/dev/ttyACM0` 通过
  serial by-id/path 指向 STC USB Serial。
- Camera OpenCV 可从 `/dev/video1` 读取 `640x480` frame，但样本仍近黑：
  `max=8`、`non_black_ratio=0.0`、`non_dark_ratio=0.0`、`edge_count=0`，
  因此 `visible_content_proven=false`。
- API `/api/radar/status` 仍能读取 latest LiDAR proof artifact，显示历史/latest
  `/scan`、raw packet 和 TF 材料存在；但本轮 live ROS topic list 没有 `/scan`，
  `ros2 topic echo --once /scan` 返回 unknown topic。因此当前 live `/scan` 未证明。
- `/root/rober/onboard/runtime/maps/trashbot_map.yaml` 和 `.pgm` 存在，但只找到
  2026-06-05 的 map lifecycle 材料；未找到同轮真实移动的 `route.csv`、keyframe
  或 manifest，`real_route_map_proven=false`。
- 本轮没有运动窗口，`physical_motion_lidar_delta_proven=false`、
  `wheel_feedback_lr_nonzero_proven=false`、`delivery_success=false`。

下一步现场 HIL gate 不变：先让现场人员提交 `/api/operator/report`，修复 camera
黑场并获得外部视频条件；只有 camera/视频、stop、LiDAR `/scan`、WAVE ROVER feedback、
安全清场和 route/map 对齐全部满足 `docs/hardware/field_hil_execution_pack.md` 后，
才允许进入受控运动。

## 2026-06-10 05:15 LiDAR scan proof refresh

`sprints/2026.06.10_05-15_lidar_scan_proof_refresh/` 在真实上位机
`root@192.168.1.11:37878` 上调用唯一允许的 LiDAR-only API refresh：
`POST /api/radar/scan-proof/refresh`，body 为
`{"start_runtime": true, "runtime_warmup_s": 6, "timeout_s": 12}`。

安全边界：

- 只允许 API-managed `o1_lidar_ros2_scan_smoke.sh` runtime 触碰 LiDAR 串口
  `/dev/ttyACM0`，实板枚举显示
  `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`。
- 未发布非零 `/cmd_vel`，未发送 direct UART `T=1` / `T=13` / `T=130` /
  `T=131`，未调用 `/api/base/manual`、`/api/base/status`、`/api/base/stop`、
  `/api/map/start`、`/api/nav2/start` 或任何底盘/导航运动 endpoint。
- `lsof /dev/ttyS5 /dev/ttyACM0` 在 refresh 前无输出；refresh 窗口内只有
  `lidar_driver` 占用 `/dev/ttyACM0`，无 `/dev/ttyS5` 行；最终清场后两者均无
  lsof 输出。

本轮将 refresh 前 live ROS graph 中缺失的 `/scan` 推进为 API-managed runtime
窗口内的新鲜 proof：

- refresh 回包：`status=refreshed`，`evidence_type=robot_runtime_material`。
- `scan_runtime_proven=true`，`ros2_runtime_proven=true`。
- `proof_state=scan_once_hz_raw_packet_tf_observed`。
- `/scan` once observed、`/scan` hz observed、`/lidar/raw_packet` once observed、
  `base_link -> laser_frame` TF observed。
- `scan_hz_average_rate_hz=14.951`。
- guard 字段保持 `sends_motion_commands=false`、
  `sends_base_motion_commands=false`、`uses_base_uart=false`、
  `publishes_cmd_vel=false`、`safe_to_control=false`。

重要边界：本轮证明的是 refresh 启动的临时 LiDAR runtime 窗口内存在当前 live
`/scan`。该 smoke runtime 结束后，最终 ROS topic list 再次没有 `/scan`，
`GET /api/radar/status` 仍报告 `blocked_reasons=["scan_continuity_not_observed"]`。
因此它不等于常驻 `/scan`、地图/AMCL/Nav2 消费、运动、物理 LiDAR delta 或送达闭环。
`physical_motion_lidar_delta_proven=false`，`wheel_feedback_lr_nonzero_proven=false`，
`delivery_success=false` 仍保持不变。

关键 artifact：

- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/lidar_scan_proof_latest.json`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/o1_lidar_ros2_scan_smoke/summary.json`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/o1_lidar_ros2_scan_smoke/scan_once.txt`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/o1_lidar_ros2_scan_smoke/scan_hz.txt`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/runtime_logs/rober_lidar_scan_proof_runtime_1781036938372.log`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts/remote_capture/final_lsof_and_runtime_processes.txt`

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
