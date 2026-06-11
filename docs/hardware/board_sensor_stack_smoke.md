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

## 2026-06-11 LiDAR Runtime Lifecycle V1

`sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/` 将真实上位机已有的
LiDAR-only smoke 脚本纳入仓库，并新增
`onboard/scripts/o1_lidar_lifecycle.sh` 作为 `/api/radar/start|stop` 的受管 runtime。

采用资料与事实边界：

- WAVE ROVER 底盘事实仍来自 `docs/vendor/VENDOR_INDEX.md`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml` 和
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：
  底盘 UART 是 newline-delimited JSON，当前实板底盘路径按既有证据为
  `/dev/ttyS5 @ 115200`，运动/反馈命令包含 `T=1/T=13/T=130/T=131`。
- 本轮 LiDAR runtime 不使用 WAVE ROVER vendor 串口；真实上位机状态和既有
  scan proof 证据显示 LiDAR 使用 `/dev/ttyACM0 @ 150000`，by-id 为
  STC USB Serial。该事实来源是 `root@192.168.1.11:37878` 现场状态与本项目
  2026-06-10/2026-06-11 artifacts，不是 WAVE ROVER 底盘文档。
- 远端已有 `/root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh` 已纳入仓库，
  远端来源 sha256 为
  `4f4dcf150989b20b6833ca7be73e2b3d78c4b027491a331af9e570731197b8ba`。

runtime lifecycle 与 scan proof refresh 的关系：

- `/api/radar/start` 通过
  `ROBER_RADAR_START_COMMAND=bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame`
  后台启动 `ros2_trashbot_hardware lidar_driver` 和
  `tf2_ros static_transform_publisher`，快速返回命令执行结果。
- `/api/radar/stop` 通过
  `ROBER_RADAR_STOP_COMMAND=bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh stop`
  只停止 lifecycle 脚本创建的进程组，不按名称杀其他 ROS2 进程。
- `/api/radar/scan-proof/refresh` 仍是证据采集入口；当 lifecycle 已 start 时，可用
  `{"start_runtime": false, "timeout_s": 12}` 只读取现有 `/scan`、`/lidar/raw_packet`
  和 TF，不再启动临时 smoke runtime。
- `ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND` 继续保留，用于没有常驻 lifecycle 时的
  临时 scan proof runtime。

真实上位机 smoke 结果：

- `POST /api/radar/start`：`command_result.executed=true`、`ok=true`，
  `failure_reason=null`。
- start 后 read-only scan proof refresh：`status=refreshed`，
  `proof_state=scan_once_hz_raw_packet_tf_observed`，
  `scan_runtime_proven=true`，`ros2_runtime_proven=true`，
  `/scan` 平均约 `15.613Hz`。
- during 阶段 `lsof /dev/ttyS5 /dev/ttyACM0` 只有 `lidar_driver` 占用
  `/dev/ttyACM0`；无 `/dev/ttyS5` 行。
- `POST /api/radar/stop`：`command_result.executed=true`、`ok=true`，
  stop 后 `/dev/ttyS5` 和 `/dev/ttyACM0` 均无 lsof/fuser 占用，lifecycle status 为
  `running=false`。

关键 artifact：

- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/summary.json`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/04_during_device_process.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/06_after_stop_device_process.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/pc_proxy/pc_proxy_radar_start_8791.json`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/pc_proxy/pc_proxy_radar_stop_8791.json`

本轮仍不是 HIL movement、Nav2 execution、真实路线或 delivery proof：
`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`
保持不变。

## 2026-06-11 PC Radar Cold Start Refresh Stabilization

`sprints/2026.06.11_10-50_pc_radar_cold_start_refresh_stabilization/`
把 PC workstation 的固定雷达 refresh body 从
`{"timeout_s":10,"runtime_warmup_s":6,"start_runtime":true}` 调整为
`{"timeout_s":20,"runtime_warmup_s":15,"start_runtime":true}`。这是 PC 代理层的
真实冷启动稳定性修正：从清理/冷状态开始时，给 LiDAR runtime、`/scan`、
`/lidar/raw_packet`、scan hz 和 TF 一个更宽的 no-motion 证据窗口。

本轮未改变 vendor/hardware facts，未修改 `docs/vendor/**`，未触碰 WAVE ROVER
UART、串口配置、firmware 或底盘控制默认值。硬件事实入口仍是
`docs/vendor/VENDOR_INDEX.md`；PC 代理只调用上位机 HTTP Robot API，不直接打开
`/dev/ttyS5` 或 `/dev/ttyACM0`。真实 smoke 仍必须证明 refresh 后
`scan_once_observed=true`、`scan_hz_observed=true`、
`raw_packet_once_observed=true`、`tf_observed=true`，且硬危险字段保持 false。

## 2026-06-11 12:45 Clean-Baseline PC Proxy Radar/Map Refresh

`sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/`
在真实上位机 `http://192.168.1.11:8787` 上通过 PC workstation 本地固定代理
`http://127.0.0.1:18788` 重跑 radar/map proof refresh。硬件事实边界仍以
`docs/vendor/VENDOR_INDEX.md` 为入口：WAVE ROVER 底盘 UART 是 vendor
newline-delimited JSON 控制链路；本轮没有发布 `/cmd_vel`，没有调用
`/api/base/manual`，没有打开或修改 `/dev/ttyS5`，也没有改 WAVE ROVER、ESP32、
Orange Pi 串口或 launch 配置。

Radar refresh 结果：

- PC proxy `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`
  返回 HTTP 200，远端 `/api/radar/scan-proof/refresh` HTTP 200。
- `latest_readback_key_values.scan_once_observed=true`
- `latest_readback_key_values.scan_hz_observed=true`
- `latest_readback_key_values.raw_packet_once_observed=true`
- `latest_readback_key_values.tf_observed=true`
- `hard_dangerous_true_fields=[]`
- direct latest readback `latest_result.generated_at=2026-06-11T05:06:46.418393Z`，
  晚于本轮 `run_started_at=2026-06-11T05:05:22.613Z`。
- 当时 radar latest contract 不输出独立 `evidence_ref`，只输出
  `artifact.path=runtime/lidar_scan_proof_latest.json`；该差异记录为
  `passed_with_radar_evidence_ref_contract_gap`，并在
  `sprints/2026.06.11_13-35_radar_evidence_ref_contract/` 后续 micro sprint 中修复。

Map refresh 结果：

- PC proxy `POST /api/robot-control/map/proof/refresh?baseUrl=http://192.168.1.11:8787`
  返回 HTTP 200，远端 `/api/map/proof/refresh` HTTP 200。
- `latest_readback_key_values.evidence_ref=o3-map-lifecycle-1781154452321`
- `latest_readback_key_values.map_once_observed=true`
- `latest_readback_key_values.map_file_observed=true`
- `latest_readback_key_values.map_metadata_observed=true`
- direct latest readback `latest_result.generated_at_ms=1781154494512`，晚于本轮开始时间。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
  `robot_control_executed=false`、`sends_motion_commands=false`、
  `sends_base_motion_commands=false`、`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`uses_base_uart=false`。

Cleanup readback：

- 本地临时 workstation API 已停止；`curl http://127.0.0.1:18788/api/health`
  失败为 expected closed，`lsof -iTCP:18788` 无监听。
- 目标侧 `ps` 过滤 `o1_lidar_ros2_scan_smoke|o1_lidar_lifecycle|slam_toolbox|map_server|lidar_driver`
  无残留 helper 行。
- 目标侧 `lsof /dev/ttyS5 /dev/ttyACM0` 与
  `fuser -v /dev/ttyS5 /dev/ttyACM0` 均无输出。

关键 artifact：

- `sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/pc_proxy/refresh_corrected_summary.json`
- `sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/pc_proxy/direct_latest_readback_after_proxy_refresh.json`
- `sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/cleanup/target_cleanup_readback.log`

## 2026-06-11 Radar Evidence Ref Contract

`sprints/2026.06.11_13-35_radar_evidence_ref_contract/` 补齐雷达 proof 的只读
证据 ID 合同。`GET /api/radar/scan-proof/latest`、`POST /api/radar/scan-proof/refresh`
和 `/api/radar/status` 现在都会暴露同一个最新 `evidence_ref/latest_evidence_ref`：

- LiDAR artifact 根节点或 `proof` 内已有 `evidence_ref` 时保持 producer 原值。
- 缺显式 ref 但有 `generated_at_ms` 时派生
  `o1-lidar-scan-proof-<generated_at_ms>`，同一 artifact 多次 readback 稳定一致。
- 只有 ISO `generated_at` 时派生安全可读 ref，移除冒号等不适合 URL/文件名消费的字符。
- artifact 缺失、坏 JSON、读取失败或根节点非 object 时不伪造成功 ref，仍按
  `missing/bad_json/read_failed/json_not_object` fail closed。

该合同只是 artifact/readback ID 补强，不改变 LiDAR 串口、WAVE ROVER 底盘 UART、
ROS2 launch 参数或运动控制边界。真实 refresh 仍只允许 no-motion scan proof：
禁止 `/cmd_vel`、`/api/base/manual`、`T=1/T=13/T=130/T=131` 和 `/dev/ttyS5`。

## 2026-06-11 Localization Reset Phase Artifact Boundary

`/api/localize/reset` 的 evidence capture 现在会在 helper 内按阶段写
`runtime/localization_reset_latest.json`。这只改变诊断材料的完整性，不改变硬件边界：

- 资料来源边界仍按 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 底盘控制是
  newline-delimited UART JSON，运动/反馈命令包含 `T=1/T=13/T=130/T=131`。
- 本轮定位 reset proof 不发送上述底盘命令，不发布 `/cmd_vel`，不打开
  `/dev/ttyS5`。
- managed localization runtime 只允许使用 LiDAR `/dev/ttyACM0 @ 150000`、
  static TF、`map_server`、`amcl` 和 lifecycle manager 采集 no-motion 证据。

## 2026-06-11 Nav2 Path Proof Device Boundary

`/api/nav2/proof/refresh` 在显式 managed no-motion path-generation opt-in 下，
会为了 AMCL/Planner 证据短暂使用 LiDAR `/dev/ttyACM0 @ 150000`、static TF、
`map_server`、`amcl`、`planner_server` 和 lifecycle manager。该路径仍禁止
打开 WAVE ROVER 底盘 UART `/dev/ttyS5`，禁止发布 `/cmd_vel`，禁止调用
`/api/base/manual`，禁止 `NavigateToPose` 或 controller/BT 执行层。验证结束后
必须检查 helper 进程、Nav2 lifecycle 进程和 LiDAR 进程是否清理干净；若
`/dev/ttyACM0` 被残留占用，需要把占用者写进 sprint artifact，而不能声明 clean pass。
- helper 被上层 timeout 打断时，upper API 会优先保留 helper 已写的
  `last_phase`、`last_successful_phase`、`current_command`、`recent_commands`、
  `package_availability`、`package_check_mode`、`package_checks_batch_ok`、
  `initialpose_published`、`amcl_pose_observed`、`localization_tf_observed` 和
  `root_causes`，再追加 timeout blocker。
- package preflight 是单次 ROS 环境 source 后的 `ros2 pkg list` 批量诊断；
  它不能再逐包阻塞 `/initialpose`、`/amcl_pose` 和 localization TF 主证据路径。

`sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/` 从上一轮
`upper_ros_quiescent=true` 基线重新跑 fresh no-motion path proof。第二次 direct
API refresh 成功生成 `map:(0.8, 0, 0)` 路径，`path_point_count=31`，
`managed_runtime_cleanup_ok=true`，结束读回确认无 `o10_amcl_nav2_runtime_proof`、
`map_server`、`amcl`、`planner_server`、`lifecycle_manager` 或 `lidar_driver`
残留，`/dev/ttyS5` 与 `/dev/ttyACM0` 无占用。本轮硬件事实边界仍按
`docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 底盘 UART 是 vendor newline-delimited
JSON 控制链路，本 proof 不打开底盘 UART、不发布 `/cmd_vel`、不调用
`/api/base/manual`。它只证明 LiDAR/static TF/map/AMCL/planner 的 no-motion
路径生成链路，不等于 NavigateToPose、固定路线执行、真实运动、HIL 或送达成功。

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

## 2026-06-11 09:05 Camera Device Visibility Probe

`sprints/2026.06.11_09-05_camera_device_visibility_probe/` 在真实上位机
`root@192.168.1.11:37878` 上复查 PC 实时图传近黑根因。本轮只访问 Robot API
camera readback、v4l2 摄像头枚举、OpenCV/ffmpeg 单帧抓取和 UVC 控制项；
未触碰 `/cmd_vel`、`/api/base/manual`、Nav2、底盘串口或雷达 runtime。

采用来源：

- `docs/vendor/VENDOR_INDEX.md`：硬件事实必须本地可追溯；本轮不新增 WAVE ROVER
  底盘、UART、电压或引脚结论。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`：vendor 上位机视频默认
  `640x480`，但没有证明 Orange Pi 当前 USB 摄像头可见内容。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`：vendor USB camera 路径使用
  OpenCV `VideoCapture(0)`；rober 现场仍必须按 `/dev/video*` 实测，不把 Raspberry Pi
  上位机假设写成 Orange Pi 默认。

真实上位机结论：

- Robot API `/api/camera/health`：`status=ready`、`video_source=auto`、
  `video_source_mode=auto`，上游 camera service 为 `http://127.0.0.1:8088`。
- `v4l2-ctl --list-devices`：`/dev/video0` 是 `cedrus` platform 视频解码器；
  `/dev/video1` 和 `/dev/video2` 属于 `USB Composite Device: DV20 USB`。
- `/dev/video1` 是唯一真实 Video Capture 节点，支持 MJPG `1280x720/640x480/480x320/1920x1080`
  和 YUYV `640x480/320x240`；`/dev/video2` 是 UVC metadata capture，不能作为 PC 图传源。
- WebRTC camera service 的 auto selection 日志显示：尝试 `/dev/video0` 打不开，
  随后选择 `/dev/video1`，因此当前近黑不是 auto 误选到 `/dev/video0` 或 `/dev/video2`。
- `/dev/video1` OpenCV 单帧：`640x480`，`mean_gray=1.0`，
  `nonblack_pixels_gt10=0`，`edge_pixels_canny=0`。
- `/dev/video1` ffmpeg 单帧交叉验证：`640x480`，`mean_gray=1.0`，
  `nonblack_pixels_gt10=0`，`edge_pixels_canny=0`。
- 临时拉高 `brightness/gain/gamma/backlight_compensation` 后仍未改善：
  `mean_gray≈0.0012`，`nonblack_pixels_gt10=0`，`edge_pixels_canny=0`。结束后
  brightness/gain/backlight 已恢复；`gamma=17` 被驱动按 step 量化为 `20`。

结论：当前 PC WebRTC 链路能传输真实帧，但真实摄像头输出本身近黑；
`visible_content_proven=false`，不能作为路线关键帧、远程可视、视觉定位或障碍识别证据。
下一步需要现场检查 DV20 摄像头镜头遮挡/保护膜/朝向/环境光/USB 摄像头本体，
或更换一个已知可见画面的 USB UVC 摄像头后重跑同一 probe。

下一步必须现场人工确认镜头盖/保护膜/遮挡、朝向、补光、USB 口和相机本体。

## 2026-06-11 10:15 Camera Visible Content Recovery

`sprints/2026.06.11_10-15_camera_visible_content_recovery/` 继续排查 PC
实时图传近黑问题。本轮只访问真实上位机 camera/WebRTC 服务、Robot API、
V4L2/USB/media readback、OpenCV/ffmpeg 单帧抓取和 PC workstation camera
preview；未触碰底盘、运动、串口、雷达、Nav2 或 vendor 文件。

采用来源与边界：

- `docs/vendor/VENDOR_INDEX.md`：硬件事实必须先查本地 vendor 资料；本轮不新增
  WAVE ROVER、UART、电压、引脚或运动结论。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、`tutorial_cn/13 在 Jupyter Lab 中显示实时画面.ipynb`
  与 `tutorial_en/13 Displaying Real-Time Video Stream in Jupyter Lab.ipynb`：
  vendor 只提供 Raspberry Pi/OpenCV/USB camera 参考，包含 `640x480` 和
  `cv2.VideoCapture` 用法；不能外推为 Orange Pi 当前设备路径或画面可见事实。

真实上位机结论：

- `trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 保持
  `active`；camera service 参数为 `--video-source auto --width 640 --height 480 --fps 15`。
- `/api/camera/health` 为 `status=ready`，WebRTC auto selection 仍选择
  `/dev/video1`；Stop/cleanup 后 `active_peer_connections=0`。
- `/dev/video1` 是 `uvcvideo` 的 `USB Composite Device: DV20 USB` capture 节点；
  `/dev/video0` 是 `cedrus` platform decoder，`/dev/video2` 是 metadata capture。
- `/dev/video1` 只有 `Input 1`，支持 MJPG `1280x720/640x480/480x320/1920x1080`
  和 YUYV `640x480/320x240`。USB descriptor 暴露 PAL/SECAM/NTSC capability，
  但本轮没有发现可通过 V4L2 input 切换解决的第二输入源。
- OpenCV 逐项尝试 YUYV/MJPG、多分辨率和亮度/增益/背光/伽马：
  默认 YUYV `mean_gray≈0.0013`、MJPG `mean_gray=1.0`、全部
  `nonblack_pixels_gt10=0`、`edge_pixels=0`。
- 极端 `auto_exposure=Manual`、`exposure_time_absolute=100000`、高亮度/对比度/增益
  只能得到很暗轮廓：`mean_gray≈1.33`、`nonblack_pixels_gt10=7315/307200`、
  `edge_pixels=597`。这证明 UVC 管线和解码可工作，但不是可用实时画面。
- ffmpeg 交叉采样 YUYV/MJPG 仍为近黑：YUYV `mean_gray≈0.019`、MJPG
  `mean_gray=1.0`，均 `nonblack_pixels_gt10=0`。
- PC workstation 通过真实页面 `打开画面 -> 关闭画面` 跑通，Chrome canvas 从
  `<video>` 采样 `320x240`：`srcObject=true`、`readyState=4`、`videoWidth=640`、
  `videoHeight=480`、`meanGray=1`、`nonBlackPixelsGt10=0`。video 区域截图仍为黑场。

结论：当前根因等级为 **物理输入侧待现场处理**。软件侧服务参数、auto 选源、
格式、分辨率、常规 UVC 控件和 PC WebRTC/Canvas 链路均已排除为主要原因；
在现场未补光、调整朝向、移除遮挡/保护膜或更换已知可见 USB UVC 摄像头前，
`visible_content_proven=false` 不能翻转。

现场动作清单：

- 检查镜头盖、保护膜、遮挡、安装朝向和是否对着暗处/车体内部。
- 在镜头前放置强光高对比目标，重跑 OpenCV default YUYV 与 PC 页面 canvas。
- 若 DV20 是采集卡而不是普通摄像头，确认 HDMI/AV 输入源已开机、输出制式/分辨率兼容。
- 换一个已知可见画面的 USB UVC 摄像头接到同一 Orange Pi USB 口，重跑
  `/api/camera/devices`、OpenCV/ffmpeg 单帧和 PC WebRTC smoke。

## 2026-06-11 10:55 Current Camera Motion Gate Readback

`sprints/2026.06.11_10-55_current_camera_motion_gate_readback/` 在真实上位机
`root@192.168.1.11:37878` 和 Robot API `http://192.168.1.11:8787` 上做了一次
非侵入 readback。本轮只读 API、SSH、v4l2 和 OpenCV 默认帧统计；未修改 PC 首屏、
onboard 代码、vendor、firmware 或硬件配置。

采用来源与边界：

- `docs/vendor/VENDOR_INDEX.md` 是硬件事实入口。
- WAVE ROVER 底盘 UART/JSON 事实继续来自
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 和
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`。
- vendor Raspberry Pi 参考串口是 `/dev/ttyAMA0` 或 `/dev/serial0`、`115200`；
  Orange Pi 现场路径必须按实测。当前 Robot API readback 显示底盘口仍为
  `/dev/ttyS5 @ 115200`。
- 本轮没有直接写 `/dev/ttyS5`。`/api/base/status` 内部执行了非运动 `T=130`
  feedback readback 并观察到 `T=1001`；这只证明反馈可见，不等于 HIL、stop、
  wheel nonzero 或运动准入。

当前 readback 结果：

- `/api/operator/report`：人工 preflight 字段为
  `operator_present=true`、`physical_clearance_confirmed=true`、
  `emergency_stop_ready=true`，`operator_report_status=ready_for_execution`；
  但 structured claims 仍为 `visible_content_proven=false`、
  `external_video_recorded=false`、`wheel_feedback_lr_nonzero_proven=false`、
  `physical_motion_lidar_delta_proven=false`、`delivery_success=false`。
- `/api/base/status`：`write_control_available=true`、`pyserial_available=true`、
  `T=1001 observed`，但顶层保持 `safe_to_control=false`、
  `primary_actions_enabled=false`、`sends_motion_commands=false`。
- `/api/base/feedback-samples/latest`：latest artifact 可加载但 stale；
  `hil_pass=false`、`safe_to_control=false`。
- `/api/camera/health`：`status=ready`，上次 WebRTC auto selection 仍选择
  `/dev/video1`，active peers 为 0。
- `/api/camera/devices` 与 `v4l2-ctl --list-devices`：`/dev/video0` 是 `cedrus`
  platform 节点，`/dev/video1` 和 `/dev/video2` 属于 `USB Composite Device: DV20 USB`；
  `/dev/video1` 是 capture 节点，`/dev/video2` 是 metadata capture。
- OpenCV 默认读 `/dev/video1` 5 帧，最后一帧 `640x480`，
  `mean_luma=0.00103515625`、`max_luma=1`、`nonblack_ratio_gt20=0.0`、
  `near_black=true`。因此当前相机仍 near-black，`visible_content_proven=false`
  不能翻转。
- `/api/radar/status`：`scan_status=fresh_scan_proof_observed`，但仍有
  `blocked_reasons=["scan_continuity_not_observed"]`。
- `/api/radar/scan-proof/latest`：latest proof 内 `/scan` once、scan hz、
  `/lidar/raw_packet` 和 TF 观察为 true，平均约 `12.482Hz`；这仍是 LiDAR
  artifact，不是运动或底盘 HIL。

只读服务和占用状态：

- `trashbot-upper-robot-api.service=active`，参数包含
  `--base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`。
- `trashbot-local-webrtc-camera.service` active；`rober-lidar.service` 和
  `trashbot-lidar.service` inactive。
- `lsof /dev/ttyS5 /dev/ttyACM0 /dev/video0 /dev/video1 /dev/video2` 无输出；
  `fuser -v` 对同一组设备也无占用输出。
- 仍观察到多组历史 `waypoint_manager`、`map_recorder`、`task_orchestrator`
  ROS 进程。本轮只记录不清理；后续进入运动或 Nav2 前需要先做进程归一和清场。

Manual non-stop gate 判定：

- `artifacts/manual_gate_decision.json` 记录 `jog_decision=not_attempted`。
- 原因：`safe_to_control=false`、`primary_actions_enabled=false`、相机仍 near-black、
  没有外部视频、wheel feedback 非零未证明、物理 LiDAR motion delta 未证明、
  `delivery_success=false` 且雷达仍缺 continuity。
- 本轮没有执行任何非零运动，没有调用远端 `/api/base/manual`，没有发布 `/cmd_vel`，
  没有直接写 `/dev/ttyS5`，也没有执行 stop。

关键 artifact：

- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/manual_gate_decision.json`
- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/camera/default_frame_stats.json`
- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/api/base_status.json`
- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/api/operator_report.json`
- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/ssh/remote_readonly_service_device_status.log`
- `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/artifacts/ssh/remote_v4l2_readonly.log`

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

## 2026-06-10 05:35 map lifecycle proof refresh

`sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/` 在真实上位机
`root@192.168.1.11:37878` 上调用唯一允许的 map lifecycle API refresh：
`POST /api/map/proof/refresh`，body 为 `{"timeout_s":60}`。本轮没有调用
`/api/map/start`、`/api/nav2/start`、`/api/nav2/proof/refresh`、`/api/base/manual`、
`/api/base/status` 或 `/api/base/stop`。

安全边界：

- 未发布非零 `/cmd_vel`，未发送 direct UART `T=1` / `T=13` / `T=130` /
  `T=131` 到 `/dev/ttyS5`。
- refresh guard 字段保持 `publishes_cmd_vel=false`、`calls_base_manual=false`、
  `sends_base_motion_commands=false`、`uses_base_uart=false`、
  `safe_to_control=false`、`delivery_success=false`。
- refresh 前 `/dev/ttyS5` 和 `/dev/ttyACM0` 均存在，`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`
  指向 `/dev/ttyACM0`；refresh 前后 `lsof /dev/ttyS5 /dev/ttyACM0` 无底盘或
  LiDAR runtime 残留。
- 结束后 `trashbot-upper-robot-api.service` 为 `active`，无 `o3_map_lifecycle_proof`、
  `slam_toolbox`、`map_saver`、`lidar_driver` 或 `ros2 launch` 残留进程。

本轮把 canonical current map lifecycle artifact 刷新为最新失败状态，而不是证明
路线地图：

- `POST /api/map/proof/refresh` 返回 HTTP 200，但 top-level `status=not_proven`，
  `failure_reason=configured_command_failed`，helper `returncode=2`。
- canonical `/root/rober/onboard/runtime/map_lifecycle_latest.json` 当前为
  `blocked_with_root_cause`，root cause 为 `/map_once_not_observed`。
- helper no-motion runtime 成功启动 `learn.launch.py` 的 LiDAR + SLAM 窗口，
  `/scan` once observed，runtime topic list 中出现 `/scan`、`/map`、`/map_metadata`、
  `/tf`、`/tf_static` 和 `slam_toolbox` topic。
- `map_once_observed=false`：`timeout 12 ros2 topic echo --once /map` 超时。
- `map_file_observed=true`：`/root/rober/onboard/runtime/maps/trashbot_map.yaml` 和
  `trashbot_map.pgm` 存在，但它们是已有文件，不是本轮新保存地图。
- `map_metadata_observed=false`：本轮没有拿到当前 map metadata。
- `map_artifact_proven=false`、`real_route_map_proven=false`、`nav2_runtime_proven=false`、
  `delivery_success=false` 均不能翻 true。

## 2026-06-10 09:15 Managed Nav2 Localization Proof

`sprints/2026.06.10_09-15_managed_nav2_localization_proof/` 把 no-motion Nav2
localization proof 从“只读 collector + 手动 runtime”收敛为单次 helper/API
显式 opt-in。硬件事实边界继续来自：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

关键事实：

- WAVE ROVER base 是 newline-delimited UART JSON。
- vendor Raspberry Pi 默认 UART 路径不是 Orange Pi 固定事实。
- 本轮 managed proof 只允许 LiDAR `/dev/ttyACM0 @ 150000`，绝不打开
  `/dev/ttyS5`。

managed runtime 只启动 localization 所需最小图：

- `lidar_driver`
- `static_transform_publisher odom -> base_link`
- `static_transform_publisher base_link -> laser_frame`
- `map_server`
- `amcl`
- `lifecycle_manager`

禁止项不变：

- planner/controller
- `ros2 action send_goal`
- compute path
- `/cmd_vel`
- `/api/base/*`
- `/api/nav2/start`
- `/api/nav2/stop`
- `autonomous.launch.py`
- base UART `/dev/ttyS5`

真实上位机 `root@192.168.1.11:37878` direct-helper 结果（`2026-06-10 08:33 CST`）：

- `managed_runtime_started=true`
- `managed_runtime_cleanup_ok=true`
- `scan_once_observed=true`
- `map_once_observed=true`
- `map_server_active=true`
- `amcl_active=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=true`
- `status=nav2_no_motion_localization_runtime_observed`
- `safe_to_control=false`
- `delivery_success=false`

remote cleanup 结果：

- `lsof /dev/ttyS5 /dev/ttyACM0` 无输出
- `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出
- `managed_runtime_process_group` 清理成功，无 orphan `ros2 topic echo/pub` /
  `tf2_echo`

`2026-06-10 08:37 CST` API 验证结果：

- 为加载新 `upper_robot_api.py`，执行过一次
  `systemctl restart trashbot-upper-robot-api.service`。
- 重启前后 service 均为 `active (running)`；本轮记录见：
  - `trashbot_upper_status_before.txt`
  - `trashbot_upper_status_after.txt`
- 默认 body `{"timeout_s":20}` 仍是 read-only：
  `managed_runtime_requested=false`、`managed_runtime_started=false`。
- managed body 成功返回 `status=refreshed`，proof 内
  `status=nav2_no_motion_localization_runtime_observed`。
- 结束后 `nav2_device_lsof.txt` 和 `nav2_device_fuser.txt` 均为空，未留下
  `/dev/ttyS5` 或 `/dev/ttyACM0` 占用。

已知剩余边界：

- `GET /api/nav2/proof/latest` 顶层仍按 software guard 返回 `status=not_proven`，
  但 `latest_proof_status` 和 `latest_*` 摘要字段已反映成功 proof。
- `GET /api/nav2/status` 当前也通过嵌套 `proof_latest` 提供最新摘要，不直接把顶层
  `status` 翻成 runtime proven。这是 API readback 合同层的保守设计，不是本轮
  localization proof 失败。

`GET /api/nav2/status` 只用于 downstream readiness readback，结果仍为
`status=not_proven`；`amcl_nav2_readiness.status=blocked_with_root_cause`，blocker 为
`map_lifecycle_proof_not_clean`、`map_once_not_observed` 和
`map_metadata_not_observed`。因此旧 `map_yaml`/`map_pgm` 只能作为材料候选，
不能解锁 AMCL/Nav2、fixed route execution、真实移动 route/map 或 delivery proof。

关键 artifact：

- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/api_map_proof_refresh_response.json`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/onboard_runtime_map_lifecycle_latest.json`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/legacy_runtime_map_lifecycle_latest.json`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/runtime_maps/trashbot_map.yaml`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/runtime_maps/trashbot_map.pgm`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/runtime_logs/rober_map_lifecycle_runtime_1781037503387.log`
- `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts/remote_capture/final_clean_after_capture_bash.txt`

## 2026-06-10 05:50 map lifecycle helper reconcile

`onboard/scripts/o3_map_lifecycle_proof.py` 已从真实上位机
`root@192.168.1.11:37878` 的 `/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`
纳入本地仓库，供 `upper_robot_api.py` 的
`Path(__file__).resolve().with_name("o3_map_lifecycle_proof.py")` 入口复现。
远端来源为 `size=16083`、`mtime=2026-06-05 12:24:57.032651159 +0800`、
`sha256=f8cffd9830ee66b5344985475c32665184a05a9ed4fb77df3ae21244c184fea3`。

该 helper 的安全边界仍是 no-motion 软件证明：

- `--help` 只走 argparse，不触碰 LiDAR、WAVE ROVER、UART 或 ROS2 runtime。
- 运行 proof 时只启动 LiDAR + SLAM no-motion 窗口，artifact 字段保持
  `publishes_cmd_vel=false`、`calls_base_manual=false`、`safe_to_control=false`、
  `delivery_success=false`。
- helper 不调用 `/api/base/manual`，不打开底盘 UART，也不发送 direct UART
  `T=1`、`T=13`、`T=130`、`T=131`。
- save map gate 仍要求先观测 `/map`；当前失败根因继续是
  `/map_once_not_observed`，因此已有 `trashbot_map.yaml` / `trashbot_map.pgm`
  不能被提升为本轮 clean map proof。

下一步不是再修 helper 入口，而是定位 SLAM/TF/topic timing：`/scan` 已观测，
但 `/map` once 与 `/map_metadata` 未在 no-motion 窗口内形成可保存的新地图。

## 2026-06-10 06:05 map lifecycle no-motion laser TF fix

`sprints/2026.06.10_06-05_map_lifecycle_tf_fix/` 修正
`onboard/scripts/o3_map_lifecycle_proof.py` 的 no-motion LiDAR+SLAM runtime：
启动 `learn.launch.py` 时同时传入 `static_laser_tf_enabled:=true` 和
`no_motion_static_odom_tf:=true`。

本次只补齐 `/map` proof 所需的 smoke-only TF 拓扑：

- `no_motion_static_odom_tf:=true` 发布 `odom -> base_link` 静态 TF。
- `static_laser_tf_enabled:=true` 发布 `base_link -> laser_frame` 静态 TF。
- LiDAR 仍只允许使用 `/dev/ttyACM0`，用于 `/scan`、`/tf`、`/map` 的 no-motion proof。
- 禁止 `/cmd_vel`、`/api/base/*`、`/api/map/start`、`/api/nav2/*` 和
  WAVE ROVER/base UART `/dev/ttyS5`。

边界：`static_laser_tf_enabled` 在这里是为 slam_toolbox 消费 `laser_frame`
scan 提供的 smoke-only 拓扑，不是机械安装标定、不是外参结论，也不等同于
可导航地图。即使 `/map` once 后续可观测，仍必须单独验证地图质量、AMCL/Nav2
readiness、fixed route 和真实现场导航。

## 2026-06-10 06:35 formal API map proof refresh

`sprints/2026.06.10_06-35_formal_map_api_refresh/` 将上一轮候选 helper
修复部署到真实上位机正式路径：
`/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`，并调用正式
`POST /api/map/proof/refresh`，body 为 `{"timeout_s":60}`。

部署方式：

- 远端 `root@192.168.1.11:37878` 可达，hostname 为 `op-z3-b6.home`，
  远端时间为 `Wed Jun 10 04:59:38 AM CST 2026`。
- `/root/rober` 和 `/root/rober/onboard` 均无 git 元数据，无法执行
  `git pull --ff-only`；因此按 fallback 备份单文件到
  `/tmp/rober_o3_map_lifecycle_proof_before_20260610_050003.py` 后覆盖正式
  helper。
- 覆盖后正式 helper sha256 为
  `cd40b1a73c1c3c936f8a08ac96fa5b8d7ff15b0ea5c47e4bb2c0452cefa6f2a6`，
  并包含 `static_laser_tf_enabled:=true` 与
  `no_motion_static_odom_tf:=true`。

安全边界：

- 本轮未调用 `/api/base/*`、`/api/map/start`、`/api/nav2/start` 或任何运动/
  导航执行接口。
- formal API map proof 的 artifact 字段保持 `publishes_cmd_vel=false`、
  `calls_base_manual=false`、`sends_base_motion_commands=false`、
  `uses_base_uart=false`、`safe_to_control=false`、`delivery_success=false`。
- pre/post/final `lsof /dev/ttyS5 /dev/ttyACM0` 与 `fuser -v` 均无占用输出；
  本轮没有打开 WAVE ROVER/base UART `/dev/ttyS5`。

正式 API 结果：

- `python3 -m py_compile` 和 `--help` 均通过。
- `POST /api/map/proof/refresh` 返回 HTTP 200；外层 `status=not_proven`、
  `software_guard=true`，这是 API 对非导航/非 HIL 材料的保守分类。
- canonical `/root/rober/onboard/runtime/map_lifecycle_latest.json` 的 runtime
  proof status 为 `map_once_artifact_metadata_observed`。
- `scan_once_observed=true`、`map_once_observed=true`、
  `map_metadata_observed=true`、`map_file_observed=true`。
- map metadata：`frame_id=map`、`resolution=0.05000000074505806`、
  `width=237`、`height=126`。
- map files：`/root/rober/onboard/runtime/maps/trashbot_map.yaml`
  和 `trashbot_map.pgm`，本地已拉回到本轮 artifacts。
- runtime log 证明正式 helper 启动了 `learn.launch.py` 的 LiDAR+SLAM 窗口，
  同时发布 `base_link -> laser_frame` 的 `static_laser_tf` 和
  `odom -> base_link` 的 `no_motion_static_odom_tf`。

已知风险：

- refresh 前 default ROS domain 已存在 `/map`，并有多组
  `waypoint_manager`、`map_recorder`、`task_orchestrator` 进程；不能确认它们是
  上一轮 map proof 残留，因此本轮只记录，不清理。
- runtime 结束时 `lidar_driver` 和 `map_recorder` 在 SIGINT 关闭路径打印
  traceback；helper stop_runtime 仍返回 `ok=true`，最终没有本轮
  `o3_map_lifecycle_proof`、`slam_toolbox`、`lidar_driver` 或 `ros2 launch`
  残留进程。
- `GET /api/nav2/status` 仍为 `status=not_proven`；它只说明 map inputs 已满足
  no-motion Nav2 collector 的前置材料，不等于地图质量、AMCL/Nav2 ready、固定路线
  或 delivery_success。

## 2026-06-10 07:05 map proof contract harden

`upper_robot_api.py` 现在把 `/api/map/proof/latest` 和
`/api/map/proof/refresh` 的顶层 readback 合同拆成两层：

- 当最新 map proof artifact 同时满足 `status=map_once_artifact_metadata_observed`、
  `scan_once_observed=true`、`map_once_observed=true`、
  `map_file_observed=true`、`map_metadata_observed=true` 时，读回会把
  `status` / `proof_state` / `ros2_runtime_proven` / `map_artifact_proven`
  直接暴露给 PC 消费。
- `safe_to_control=false`、`delivery_success=false`、
  `primary_actions_enabled=false`、`robot_control_executed=false`、
  `sends_motion_commands=false`、`sends_base_motion_commands=false`、
  `uses_base_uart=false` 仍然保持关闭。
- artifact 缺失、坏 JSON、`status` 非 clean，或任一 required observation 为 false 时，
  继续 fail closed 为 `not_proven`。
- `GET /api/map/status` 的 `proof_latest` 摘要会跟随同一合同，供 PC 点灯，
  但它仍然不代表 Nav2 可用、真实路线、发车许可或 delivery 成功。

## 2026-06-10 07:05 Nav2 no-motion collector reconcile

`sprints/2026.06.10_07-05_nav2_no_motion_collector_reconcile/` 将真实上位机
`root@192.168.1.11:37878` 上的
`/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 拉回本地
`onboard/scripts/o10_amcl_nav2_runtime_proof.py`，作为
`/api/nav2/proof/refresh` 使用的同目录 no-motion helper。本轮只做 helper
reconcile、静态 guard 测试和正式 API readback，不启动 path execution，不发送
Nav2 goal，不发布 `/cmd_vel`。

远端来源：

- `size=19418`
- `mtime=2026-06-05 16:15`
- `sha256=b79f4471dec458479425abbb44fad438334055bc8a94e30d0a1372e4ccccb117`

正式 API 结果：

- `POST /api/nav2/proof/refresh` 返回 `curl: (52) Empty reply from server`，未产生新的
  `nav2_lifecycle_latest.json`；`trashbot-upper-robot-api.service` 随后由 systemd
  恢复为 `active`。
- `GET /api/nav2/proof/latest` 和 `GET /api/nav2/status` 均返回 HTTP 200，但读到的
  canonical artifact 仍是 2026-06-05 16:44 的旧 blocked 结果。
- `GET /api/nav2/status` 的 `amcl_nav2_readiness.status` 为
  `map_inputs_ready_for_no_motion_nav2_collector`，说明当前 map proof 已满足下一步
  collector 输入，不代表 AMCL/Nav2 runtime ready。
- 旧 `nav2_lifecycle_latest.json` 的 blockers 包括 `nav2_amcl_missing`、
  `nav2_planner_missing`、`nav2_controller_missing`、`map_server_lifecycle_not_active`、
  `amcl_lifecycle_not_active`、`planner_lifecycle_not_active`、
  `controller_lifecycle_not_active`、`/scan_once_not_observed`、
  `/map_once_not_observed` 和 `/amcl_pose_once_not_observed`。
- `latest_map_server_active=false`、`latest_amcl_active=false`、
  `latest_planner_active=false`、`latest_controller_active=false`、
  `latest_scan_consumed=false`、`latest_map_consumed=false`。

安全边界：

- 本轮未调用 `/api/base/*`、`/api/map/start`、`/api/nav2/start` 或任何运动/
  导航执行接口。
- 本轮只读 `lsof/fuser` 检查 `/dev/ttyS5` 和 `/dev/ttyACM0`；未打开
  WAVE ROVER/base UART `/dev/ttyS5`。
- API readback 和旧 artifact 的 guard 均保持 `publishes_cmd_vel=false`、
  `calls_base_manual=false`、`uses_base_uart=false`、`safe_to_control=false`、
  `delivery_success=false`。

## 2026-06-10 07:35 Nav2 package install probe

`sprints/2026.06.10_07-35_nav2_package_install_probe/` 只处理真实上位机
`root@192.168.1.11:37878` 的 Nav2 runtime 包缺失层，不启动运动或导航执行。
本轮先记录 hostname/date/OS/ROS distro、APT sources、`apt-cache policy`、
`apt-get -s install` 和当前包状态；dry-run 显示只会新增 9 个 ROS 包，
`0 upgraded, 0 to remove`，因此执行：

```bash
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-upgrade \
  ros-humble-nav2-amcl \
  ros-humble-nav2-planner \
  ros-humble-nav2-controller \
  ros-humble-nav2-map-server
```

安装结果：

- `ros-humble-nav2-map-server` 原本已安装，未升级。
- 新增 `ros-humble-nav2-amcl`、`ros-humble-nav2-planner`、
  `ros-humble-nav2-controller` 及其 ROS runtime 依赖。
- post individual `ros2 pkg prefix` 确认 `nav2_amcl`、`nav2_planner`、
  `nav2_controller`、`nav2_map_server` 均位于 `/opt/ros/humble`。
- 旧 blocker `nav2_amcl_missing`、`nav2_planner_missing`、
  `nav2_controller_missing` 已从最新 no-motion proof 中消失。

本轮随后只调用允许的 no-motion API：

```bash
curl -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H 'Content-Type: application/json' \
  -d '{"timeout_s":20}'
curl -sS http://127.0.0.1:8787/api/nav2/proof/latest
curl -sS http://127.0.0.1:8787/api/nav2/status
```

正式 proof 仍是 `blocked_with_root_cause`，这是预期前进而不是 ready：

- lifecycle 未 active：`map_server_lifecycle_not_active`、
  `amcl_lifecycle_not_active`、`planner_lifecycle_not_active`、
  `controller_lifecycle_not_active`。
- topic/material 未观测：`/scan_once_not_observed`、`/map_once_not_observed`、
  `/amcl_pose_once_not_observed`。
- `publishes_cmd_vel=false`、`calls_base_manual=false`、
  `uses_base_uart=false`、`safe_to_control=false`、`delivery_success=false`。

安全复查：pre/install/post/final `lsof /dev/ttyS5 /dev/ttyACM0 || true` 和
`fuser -v /dev/ttyS5 /dev/ttyACM0 || true` 均无进程行。本轮没有打开 WAVE
ROVER/base UART `/dev/ttyS5`，没有调用 `/api/base/*`、`/api/map/start`、
`/api/nav2/start`、`/api/nav2/stop`，没有启动 autonomous launch，没有发送 goal。

下一步应单独处理 Nav2 lifecycle/runtime 启动与同图 `/scan`、`/map`、
`/amcl_pose` 观测，不应把本轮 package install 视为 AMCL/Nav2 ready、
path generation、fixed-route execution 或 delivery_success。

## 2026-06-10 07:55 Nav2 no-motion lifecycle smoke

`sprints/2026.06.10_07-55_nav2_no_motion_lifecycle_smoke/` 在真实上位机
`root@192.168.1.11:37878` 上运行 no-motion Nav2 lifecycle/runtime smoke。
本轮不使用 `autonomous.launch.py`，不启动 `esp32_bridge`、`task_orchestrator`
或任何 goal/path execution。

正式 `nav2_bringup` 路径在包检查阶段被阻塞：

- `nav2_bringup`、`nav2_lifecycle_manager`、`nav2_navfn_planner`、
  `nav2_regulated_pure_pursuit_controller` 均 `Package not found`。
- `apt-get -s install ros-humble-nav2-bringup` 显示
  `5 upgraded, 164 newly installed, 0 to remove and 317 not upgraded`，
  会拉入完整 `ros-humble-navigation2`、OpenCV/GDAL 等大量依赖并升级系统库；
  本轮未安装。

fallback smoke 启动独立 `/tmp` 进程组，仅运行：

- `lidar_driver`：`/dev/ttyACM0 @ 150000`，发布 `/scan`。
- static TF：`base_link -> laser_frame` 与 `odom -> base_link`，均为零位姿
  smoke-only，不代表机械标定或真实里程计。
- 直接 executable：`map_server`、`amcl`、`planner_server`、`controller_server`。

正式 `/api/nav2/proof/refresh -d '{"timeout_s":20}'` 结果：

- `status=blocked_with_root_cause`
- `scan_once_observed=true`，旧 `/scan_once_not_observed` blocker 已消失。
- `map_server_active=false`、`amcl_active=false`、`planner_active=false`、
  `controller_active=false`。
- `map_once_observed=false`、`amcl_pose_observed=false`、
  `path_generation_ready=false`。
- `publishes_cmd_vel=false`、`calls_base_manual=false`、
  `uses_base_uart=false`、`delivery_success=false`。

read-only lifecycle 状态均为 `unconfigured [1]`。这说明当前节点可被直接拉起，
但缺 `nav2_lifecycle_manager`/正式 bringup 后不会自动 active；本轮也没有调用
lifecycle transition service。final cleanup 后本轮 `lidar_driver`、Nav2 server、
static TF 进程无残留，`/dev/ttyS5` 与 `/dev/ttyACM0` 的 `lsof/fuser` 均无输出。

## 2026-06-10 08:15 Nav2 lifecycle activation probe

`sprints/2026.06.10_08-15_nav2_lifecycle_activation_probe/` 继续真实上位机
`root@192.168.1.11:37878` 的 no-motion Nav2 readiness 采集。本轮仍不使用
`autonomous.launch.py`，不启动 `esp32_bridge`、`task_orchestrator` 或任何
goal/path execution。

窄包安装已执行，dry-run 与实际安装均为：

- 新增 `ros-humble-nav2-lifecycle-manager`、
  `ros-humble-nav2-navfn-planner`、
  `ros-humble-nav2-regulated-pure-pursuit-controller`。
- 额外新增 ROS 依赖 `ros-humble-diagnostic-updater`。
- `0 upgraded, 4 newly installed, 0 to remove`；未升级或卸载系统包。
- 安装后 `nav2_lifecycle_manager`、`nav2_navfn_planner`、
  `nav2_regulated_pure_pursuit_controller`、`nav2_amcl`、`nav2_planner`、
  `nav2_controller`、`nav2_map_server` 均可由 `ros2 pkg prefix` 定位到
  `/opt/ros/humble`。

手动 no-motion runtime 使用 `/dev/ttyACM0 @ 150000` LiDAR、`base_link -> laser_frame`
与 `odom -> base_link` static TF、direct `map_server/amcl/planner_server/controller_server`
以及 `nav2_lifecycle_manager`。结果：

- `map_server_active=true`：手动窗口内 `map_server` 读取
  `/root/rober/onboard/runtime/maps/trashbot_map.yaml` 与 `.pgm` 后进入
  `active [3]`。
- `amcl_active=true`：手动窗口内 `amcl` 进入 `active [3]`，但因本轮禁止
  `/initialpose`，持续提示需要 initial pose，未发布 `/amcl_pose` 或 localization
  transform。
- `planner_active=false`：`global_costmap` 卡在 `activating [13]`，日志反复提示
  `Timed out waiting for transform from base_link to map`。
- `controller_active=false`：controller 插件加载成功，但 lifecycle 停在
  `inactive [2]`，未进入 active。
- `scan_once_observed=true`：手动窗口内 `/scan` once 成功。
- `map_once_observed=false`、`amcl_pose_observed=false`：8 秒 echo 均超时。

`/cmd_vel` 安全证据：

- 手动窗口中 `/cmd_vel` topic 出现，publisher 为 `controller_server`。
- `timeout 8 ros2 topic echo /cmd_vel` 未收到消息，`publishes_cmd_vel=false`
  仍成立。
- 本轮未调用 `ros2 action send_goal`、compute path service、`/initialpose`、
  `/api/base/*`、`/api/map/start`、`/api/nav2/start` 或 `/api/nav2/stop`。
- 未打开 WAVE ROVER/base UART `/dev/ttyS5`；只读 `lsof/fuser` 检查。

正式 `/api/nav2/proof/refresh -d '{"timeout_s":20}'` 在清场后调用，返回
`status=blocked_with_root_cause`、`failure_reason=configured_command_failed`。
formal collector 是 read-only existing ROS graph collector；它不会启动本轮手动
stack，因此 canonical artifact 仍记录 `map_server_active=false`、
`amcl_active=false`、`planner_active=false`、`controller_active=false`、
`scan_once_observed=false`、`map_once_observed=false`、`amcl_pose_observed=false`。
`GET /api/nav2/proof/latest` 与 `GET /api/nav2/status` 均 HTTP 200，guard 字段保持
`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、
`safe_to_control=false`、`delivery_success=false`。

清场结果：本轮手动 stack PGID 与 runner PGID 均已清理；final
`lsof /dev/ttyS5 /dev/ttyACM0` 和 `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出。
结论是：窄包安装有效推进到 lifecycle/plugin 可启动层，但 Nav2 ready 仍被
AMCL initial pose 边界和 `map -> base_link` TF 缺失阻塞，不构成 path generation、
fixed-route execution、safe_to_control 或 delivery_success。

## 2026-06-10 08:45 Nav2 initialpose no-motion proof boundary

`sprints/2026.06.10_08-45_nav2_initialpose_no_motion_proof/` 将 08:15 blocker
拆成显式 opt-in 的 localization proof。`POST /api/nav2/proof/refresh` 默认 body
不传 `initialpose_opt_in` 时仍是 read-only collector，不发布 `/initialpose`。

允许的 opt-in body 形状：

```json
{
  "timeout_s": 20,
  "initialpose_opt_in": true,
  "initialpose_x": 0.0,
  "initialpose_y": 0.0,
  "initialpose_yaw": 0.0,
  "initialpose_frame_id": "map"
}
```

启用 opt-in 后，helper 只在 no-motion 窗口内向 `/initialpose` 发布一次
`geometry_msgs/msg/PoseWithCovarianceStamped`，用于 AMCL 初始定位证据。之后只读采集
`/amcl_pose`、`map -> odom`、`map -> base_link`、lifecycle 和 topic/node 信息。

安全边界保持不变：

- 不发布 `/cmd_vel`。
- 不调用 `/api/base/*`，也不调用 `/api/nav2/start` 或 `/api/map/start`。
- 不发送 Nav2 goal，不调用 compute path action/service。
- 不打开 WAVE ROVER/base UART `/dev/ttyS5`；底盘 UART/JSON 事实仍以
  `docs/vendor/VENDOR_INDEX.md` 为准，本 proof 不消费该链路。
- Artifact 必须记录 `initialpose_publish_attempted`、`initialpose_published`、
  pose 数值、`/amcl_pose`、TF listener 结果，并保持 `safe_to_control=false`、
  `publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、
  `delivery_success=false`。

因此本入口最多证明 AMCL no-motion localization material，不证明 Nav2 path
generation、controller output、真实底盘运动、fixed-route execution、HIL 或 delivery
success。

## 2026-06-10 09:05 Nav2 path generation opt-in boundary

在 08:45 localization proof 之后，现场 no-motion proof 继续允许显式 opt-in 的
planner `ComputePathToPose` 一次性计算，但仍然不是运动验证：

- 默认不调用 `ComputePathToPose`，也不改变 `safe_to_control=false`。
- 只有在 managed runtime + initialpose/localization 已成立时，才允许 path generation。
- 不允许 `NavigateToPose`、`FollowPath`、`/cmd_vel`、`/api/base/*` 或 `bt_navigator`。
- `/dev/ttyS5` 仍然只做只读占用检查，不能被打开写入。
- `/api/nav2/proof/refresh` 会先 source ROS Humble setup 再拉起 helper，避免
  systemd 服务环境把 `rclpy` 依赖吞掉；但这不改变默认 no-motion 边界。

这一步输出的仍然只是 planner proof 和 path artifact，不是 path execution、
fixed-route execution、delivery success 或 HIL pass。

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

## 2026-06-11 02:45 PC Map Runtime Controls V1

本轮将 `POST /api/map/start` 与 `POST /api/map/save` 接到上位机内置
`o3_map_lifecycle_proof.py` no-motion helper。helper 只启动
LiDAR + SLAM，观测 `/scan` 和 `/map`，调用 `/trashbot/save_map`，然后清理
本轮 launch 进程组；它不发布 `/cmd_vel`，不调用 `/api/base/*`，不打开
WAVE ROVER 底盘 UART `/dev/ttyS5`。

实板验证目标：`root@192.168.1.11:37878`，上位机 API 为
`http://127.0.0.1:8787`。部署后远端 `python3 -m py_compile
onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py`
通过，`trashbot-upper-robot-api.service` 重启后 `active`。

关键证据：

- `POST /api/map/save` body 使用
  `{"map_name":"pc_runtime_v1","artifact_path":"/tmp/ignored.yaml"}`。
- 返回 `status=map_once_artifact_metadata_observed`、
  `command_result.executed=true`、`command_result.ok=true`、
  `artifact_path_ignored=true`。
- 本轮生成 `/root/rober/onboard/runtime/maps/pc_runtime_v1.yaml` 和
  `/root/rober/onboard/runtime/maps/pc_runtime_v1.pgm`。
- `GET /api/map/list` 可列出 `pc_runtime_v1.yaml/pgm`。
- `GET /api/map/proof/latest` 顶层读回
  `scan_once_observed=true`、`map_once_observed=true`、
  `map_file_observed=true`、`map_metadata_observed=true`。
- pre/during/post `lsof /dev/ttyS5 /dev/ttyACM0` 与最终 `fuser` 清场均未显示
  `/dev/ttyS5` 占用；during 只观察到本轮 `o3_map_lifecycle_proof.py` 和
  helper 启动的 LiDAR/SLAM runtime。
- 最终复查 `o3_map_lifecycle_proof.py`、`slam_toolbox`、`lidar_driver`
  无残留，`trashbot-upper-robot-api.service` 仍为 `active`。

PC 代理 smoke：

- `POST /api/robot-control/map/start?baseUrl=http://192.168.1.11:8787`
  返回 `proxy_status=lifecycle_forwarded`、`remote_http_status=200`、
  `command_result.executed=true`、`command_result.ok=true`。
- `POST /api/robot-control/map/save?baseUrl=http://192.168.1.11:8787`
  首轮暴露 `/map_once_not_observed` 抖动；helper 将 `/map` 观测窗口从 12s
  放宽到 20s、save service 窗口从 8s 放宽到 12s 后，rerun 返回
  `proxy_status=lifecycle_forwarded`、`command_result.ok=true`。
- 最终生成 `pc_proxy_start.yaml/pgm` 与 `pc_proxy_save2.yaml/pgm`，并再次确认
  `/dev/ttyS5`、`/dev/ttyACM0` 无占用，目标进程无残留。

证据路径：

- `sprints/2026.06.11_02-45_pc_map_runtime_controls/artifacts/remote_map_save_smoke.log`
- `sprints/2026.06.11_02-45_pc_map_runtime_controls/artifacts/pc_proxy_map_start.json`
- `sprints/2026.06.11_02-45_pc_map_runtime_controls/artifacts/pc_proxy_map_save_rerun.json`
- `sprints/2026.06.11_02-45_pc_map_runtime_controls/artifacts/remote_final_cleanup_after_proxy.log`

边界：本轮证明 PC/上位机可以受控触发 no-motion map runtime，并生成地图文件。
它不证明地图质量、AMCL 定位可用、Nav2 可行驶、固定路线执行、真实底盘运动、
WAVE ROVER HIL、robot ACK 或 delivery success。WAVE ROVER 底盘 UART 事实仍以
`docs/vendor/VENDOR_INDEX.md` 及其指向的 vendor 文件为准；本轮没有触碰
`/dev/ttyS5 @ 115200`、`T=1/T=13/T=130/T=131` 或 JSON newline 底盘命令。

## 2026-06-11 03:25 PC Localization Reset Controls V1

本轮新增高级诊断专用 `POST /api/localize/reset` 和
`POST /api/robot-control/localize/reset?baseUrl=<upper-api>`。该入口复用
`o10_amcl_nav2_runtime_proof.py`，默认写
`/root/rober/onboard/runtime/localization_reset_latest.json` 或配置的
`runtime/localization_reset_latest.json`。helper 只允许短暂 managed localization
runtime、发布一次 `/initialpose`、观察 `/amcl_pose` 和 localization TF。

硬件/vendor 边界：

- WAVE ROVER base UART、newline-delimited JSON、vendor Raspberry Pi 默认
  `115200` 资料来源是 `docs/vendor/VENDOR_INDEX.md` 及其指向的
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `config.yaml`、`WAVE_ROVER_V0.9/json_cmd.h`。
- 项目真实上车证据采用底盘 UART `/dev/ttyS5 @ 115200`；该事实只作为本轮
  blocked/safety boundary 写入文档和响应。
- 本轮不打开 `/dev/ttyS5`，不发送 `T=1/T=13/T=130/T=131`，不调用
  `/api/base/manual`，不发布 `/cmd_vel`，不调用 Nav2 start/stop 或
  `NavigateToPose`。
- `/dev/ttyACM0` 只可能被 helper 的 LiDAR/localization runtime 使用；最终 smoke
  必须检查无 `o10_amcl_nav2_runtime_proof`、`lidar_driver`、`map_server`、
  `amcl`、`planner_server` 残留，以及 `/dev/ttyS5`、`/dev/ttyACM0` 无异常占用。

`GET /api/localize/proof/latest` 必须摘要：`initialpose_published`、
`amcl_pose_observed`、`localization_tf_observed.map_to_odom`、
`localization_tf_observed.map_to_base_link`、`managed_runtime_started`、
`managed_runtime_cleanup_ok` 和 `root_causes`。所有安全字段继续保持 false。

## 2026-06-11 04:30 Localization TF Chain Diagnostics

本轮不改变硬件边界，只把 no-motion localization reset 的 TF 诊断从最终布尔值
下钻到链路段。helper 的 managed runtime 仍只允许启动 LiDAR `/dev/ttyACM0`、
`map_server`、`amcl`、lifecycle manager 以及两个 static transform publisher：

- `odom -> base_link`
- `base_link -> laser_frame`

artifact 新增稳定字段：

- `tf_chain_observed.map_to_odom`
- `tf_chain_observed.odom_to_base_link`
- `tf_chain_observed.base_link_to_laser_frame`
- `tf_chain_observed.map_to_base_link`
- `tf_chain_diagnostics`
- `tf_failure_classification`

如果 `map->base_link` 仍未观测，root cause 必须尽量下钻为
`map_to_base_link_blocked_by_missing_map_to_odom`、
`map_to_base_link_blocked_by_missing_odom_to_base_link`、
`map_to_base_link_frame_naming_mismatch` 或
`map_to_base_link_tf2_timeout_or_chain_timing`。这只证明 TF/source/timing
定位材料，不允许用更长 timeout 掩盖问题，也不触发 `NavigateToPose`、
`/cmd_vel`、`/api/base/*`、`/dev/ttyS5` 或 WAVE ROVER `T=1/T=13/T=130/T=131`。

## 2026-06-11 04:45 AMCL TF Source Diagnostics

本轮仍是 no-motion localization evidence capture，不新增任何底盘或 WAVE ROVER
动作。helper 在 `/initialpose` 与 `/amcl_pose` 之后、慢 `tf2_echo` 之前，先采集
轻量 source/timing 快照：

- `/tf` 和 `/tf_static` 是否出现在 topic graph。
- `/tf_static` 中是否能看到 `odom -> base_link`、`base_link -> laser_frame`。
- `/tf` 中是否能看到 AMCL 广播的 `map -> odom`。
- `/amcl_pose.header.frame_id`、`/amcl` publishers/subscribers。
- `/amcl` 实际参数：`tf_broadcast`、`global_frame_id`、`odom_frame_id`、`base_frame_id`。

artifact/readback 新增 `tf_topics_observed`、`tf_static_observed`、
`tf_frame_inventory`、`amcl_pose_frame_id`、`amcl_node_publishers`、
`amcl_node_subscribers`、`amcl_tf_broadcast_param`、`amcl_frame_params`、
`map_frame_observed`、`odom_frame_observed` 和 `amcl_tf_root_cause`。这些字段只用于
定位 AMCL/TF source/timing root cause；安全边界继续禁止 `/cmd_vel`、`/api/base/*`、
`NavigateToPose`、`/dev/ttyS5` 和 WAVE ROVER `T=1/T=13/T=130/T=131`。

## 2026-06-11 05:05 AMCL Params And Static TF Source

本轮继续沿用 `docs/vendor/VENDOR_INDEX.md` 的硬件边界：WAVE ROVER 底盘 UART
和运动/反馈命令仍不参与，helper 只允许 no-motion `/initialpose`、AMCL、LiDAR
`/dev/ttyACM0 @ 150000` 和 TF 诊断。

为避免用更长 timeout 掩盖问题，AMCL 参数和 graph 现在优先由短生命周期 rclpy
probe 读取，而不是串行调用多条 ROS CLI。artifact/readback 新增或填实：

- `amcl_param_probe_ok`
- `amcl_node_info_observed`
- `amcl_log_tail`
- `managed_static_tf_processes`
- `static_tf_source_observed`
- `tf_source_root_cause_detail`
- `amcl_broadcast_conditions`

`managed_static_tf_processes` 必须记录两个 no-motion static publisher：
`odom -> base_link` 和 `base_link -> laser_frame`。若进程存在但 `/tf_static`
仍未观测到对应边，root cause 应落到 QoS/timing/source observation；若进程不存在，
root cause 应落到 managed runtime 启动或 shell 启动顺序。`amcl_broadcast_conditions`
用于区分 AMCL `map -> odom` 未广播是参数不生效、`/scan`/`/map` 输入缺失、
static TF 输入缺失，还是 AMCL 自身广播条件未满足。

## 2026-06-11 05:25 Static TF Broadcaster Evidence

本轮继续沿用 `docs/vendor/VENDOR_INDEX.md` 的硬件事实边界：WAVE ROVER 底盘
UART 是 newline-delimited JSON 控制链路，运动/反馈命令 `T=1/T=13/T=130/T=131`
不参与本轮 no-motion localization reset。真实上车 smoke 只允许 helper 临时打开
LiDAR `/dev/ttyACM0 @ 150000`，不打开 `/dev/ttyS5`，不调用 `/api/base/*`，
不发布 `/cmd_vel`，不触发 `NavigateToPose` 或 HIL。

为消除两个独立 `static_transform_publisher` 的 `/tf_static` latch/timing 抖动，
helper 的 managed runtime 改为单个 rclpy `managed_static_tf_broadcaster`：

- 同一个 `StaticTransformBroadcaster` 同时发布 `odom -> base_link` 与
  `base_link -> laser_frame`。
- `managed_static_tf_processes.source_strategy` 记录
  `single_rclpy_static_transform_broadcaster_transient_local`。
- `managed_static_tf_processes.observed_roles` 仍列出
  `static_tf_odom_base` 与 `static_tf_base_laser`，便于和旧 readback 字段兼容。

最终真实上位机 evidence 保存在
`sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/`：

- `localize_reset_response.final.json`
- `localize_proof_latest.final.json`
- `localization_reset_latest.final.remote.json`
- `final_process_device_check.log`

关键结果：

- `status=nav2_no_motion_localization_runtime_observed`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `/tf_static` 同时观测到 `odom -> base_link` 和 `base_link -> laser_frame`
- `tf_chain_observed.map_to_base_link=true`
- `root_causes=[]`
- 清场后 `trashbot-upper-robot-api.service=active`，目标 ROS/helper 进程无残留，
  `/dev/ttyS5`、`/dev/ttyACM0` 均无 `fuser/lsof` 占用输出。

## 2026-06-11 05:45 Structured Operator HIL Report Intake

本轮只升级 `/api/operator/report` 的现场材料 intake，不新增任何会发送运动命令的
行为。硬件边界继续沿用 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER
`base_ctrl.py`、`config.yaml` 和 `json_cmd.h`：底盘 UART 是 newline-delimited JSON，
运动/反馈命令 `T=1/T=13/T=130/T=131` 不参与本轮 report smoke。

新的 report schema 会把以下人工材料字段统一归一化到 `structured_hil_claims`：
`external_video_recorded`、`external_video_ref`、`visible_content_proven`、
`camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`、
`physical_motion_lidar_delta_proven`、`scan_delta_ref`、`real_route_map_proven`、
`route_map_ref`、`delivery_success` 和 `site_state`。

安全边界：

- `/api/operator/report` POST/GET 只写读 JSON artifact，不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`，不打开 `/dev/ttyS5`，不启动 Nav2 goal。
- 即使 `structured_hil_claims.delivery_success=true`，API 顶层仍固定
  `operator_report_material_only=true`、`hil_pass=false`、`delivery_success=false`、
  `report_replaces_stop_status_ack_or_hil=false`、`sends_motion_commands=false` 和
  `opens_serial=false`。
- 真实 HIL 通过仍必须由外部视频、相机 artifact、`T=1001` feedback、scan delta、
  route/map artifact、stop/API restore 记录共同证明；report 只是一份材料索引。

## 2026-06-11 08:05 Map Lifecycle `/scan` Observation Stabilization

本轮只稳定 no-motion LiDAR + SLAM map lifecycle proof，不新增底盘运动。硬件边界
继续以 `docs/vendor/VENDOR_INDEX.md` 为入口；WAVE ROVER UART `/dev/ttyS5`、
`/cmd_vel`、`/api/base/manual` 和 `T=1/T=13/T=130/T=131` 均不参与。本轮只使用
既有真实上位机 evidence 中的 LiDAR `/dev/ttyACM0 @ 150000`。

上一轮失败 artifact 显示 `/scan` 已出现在 topic list，`/map` 已观测，地图
YAML/PGM 也已生成，但单次 `timeout 8 ros2 topic echo --once /scan` 超时，导致
helper root cause 为 `/scan_once_not_observed`。因此问题归类为 `/scan` clean proof
采样窗口抖动，而不是 SLAM 完全未消费雷达。

`o3_map_lifecycle_proof.py` 现在保留 `/scan_once_observed=true` 的硬 gate，但用
`ros2 topic echo --once --qos-profile sensor_data /scan` 做最多 2 次独立采样，并在
artifact 中记录 `attempts`、`attempt_count` 和
`stable_observation_strategy=retry_topic_echo_once`。这不会绕过 `/scan` proof；只有
真实 echo 到 LaserScan 文本时才算 clean pass。

真实上位机验证：

- direct `POST /api/map/save`，`map_name=scan_stabilize_fixed_20260611_0756`：
  `command_result.ok=true`，`scan_once_observed=true`，`map_once_observed=true`，
  `map_file_observed=true`，`map_metadata_observed=true`。
- PC proxy `POST /api/robot-control/map/save`，
  `map_name=pc_proxy_scan_stabilize_20260611_0758`：
  `proxy_status=lifecycle_forwarded`，`remote_http_status=200`，
  `command_result.ok=true`。
- 远端 `/api/map/list` 列出
  `pc_proxy_scan_stabilize_20260611_0758.yaml` 与
  `pc_proxy_scan_stabilize_20260611_0758.pgm`。
- 最终 `lsof`/`fuser` 对 `/dev/ttyS5`、`/dev/ttyACM0` 无输出，目标
  helper/SLAM/LiDAR 进程无残留。

## 2026-06-11 10:35 PC Manual HIL Gate Current Evidence

`sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/` 通过 PC
workstation proxy 对真实上位机 `http://192.168.1.11:8787` 复核手动移动 HIL gate。
本轮继续沿用 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER 资料：
底盘控制是 UART newline-delimited JSON，运动/反馈命令包括 `T=1/T=13/T=130/T=131`；
PC workstation 只调用上位机 HTTP API，不直接写 `/dev/ttyS5`，不发布 `/cmd_vel`。

当前 `/api/operator/report`、`/api/base/status`、
`/api/base/feedback-samples/latest`、`/api/radar/status` 和
`/api/radar/scan-proof/latest` 均可读，但 manual 非 stop gate 仍为 `blocked`：

- `operator_present=true`
- `physical_clearance_confirmed=true`
- `emergency_stop_ready=true`
- `external_video_recorded=false`
- `visible_content_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `physical_motion_lidar_delta_proven=false`

因此本轮未执行真实非零运动。PC proxy stop safety smoke 成功转发固定
`/api/base/stop`，随后一次 `forward speed=0.12 duration_ms=800` manual 请求被本地
HTTP 400 拒绝，`failure_reason=operator_report_preflight_required`，
`remote_http_status=null`，证明未调用远端 `/api/base/manual`。

清场 readback 显示 `trashbot-upper-robot-api.service` 和
`trashbot-local-webrtc-camera.service` 均为 active，`8088/8787` 正常监听，
`/dev/ttyS5`、`/dev/ttyACM0` 的 `lsof`/`fuser` 无占用输出。本轮结论不等于 HIL
movement pass；下一步现场必须补外部视频、可见相机 artifact、轮速反馈引用和 LiDAR
运动 delta 引用后，才允许通过 PC proxy 做 exactly one 低速短时 jog。

## 2026-06-11 11:05 Upper ROS Quiescence Baseline

`sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/` 在真实上位机
`root@192.168.1.11:37878` 上做了一轮不运动 ROS 清场基线。硬件事实入口仍是
`docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 底盘控制是 UART newline-delimited JSON，
本轮没有发布 `/cmd_vel`、没有调用 `/api/base/manual`、没有写 `/dev/ttyS5`，也没有
发送 `T=1/T=13/T=130/T=131` 等底盘指令。

清场前 `ps` 和 `ros2 node list` 显示三组历史 ROS 应用进程残留：

- `waypoint_manager`：PID `89708`、`90724`、`95878`
- `map_recorder`：PID `89710`、`90726`、`95880`
- `task_orchestrator`：PID `89714`、`90730`、`95884`

这些进程均为 PPID 1 的历史 ROS 应用残留。清场只对上述 9 个精确 PID 发送
SIGINT；5 秒后目标进程已全部退出，未进入 SIGTERM。未执行 `killall python3`，
未杀 `trashbot-upper-robot-api.service`、`trashbot-local-webrtc-camera.service`、
`frpc`、`sshd`、`ros2 daemon`、LiDAR lifecycle 或系统服务。

清场后基线：

- `upper_ros_quiescent=true`
- `ps -eo pid,ppid,stat,cmd` 过滤 `waypoint_manager|map_recorder|task_orchestrator`
  无输出。
- `ros2 node list` 无 `waypoint_manager`、`map_recorder`、`task_orchestrator`。
- `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video0`、`/dev/video1`、`/dev/video2` 的
  `lsof`/`fuser` 无占用输出。
- `trashbot-upper-robot-api.service=active`、
  `trashbot-local-webrtc-camera.service=active`，`sshd` 保持 active；`frpc` 进程仍在
  `ss` UDP 摘要中可见但 `frpc.service=inactive`，本轮未触碰。
- Robot API 只做 readback：`/api/status`、`/api/base/status`、
  `/api/camera/health`、`/api/radar/status`、`/api/radar/scan-proof/latest`、
  `/api/operator/report`。返回材料继续显示 `safe_to_control=false`、
  `delivery_success=false`、`primary_actions_enabled=false`。

artifact：

- `sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/artifacts/pre_clear_readback.log`
- `sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/artifacts/clear_actions.log`
- `sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/artifacts/post_clear_readback.log`

该基线只说明后续 LiDAR、camera、map、Nav2/path proof 或运动实跑前，上位机没有这三类
历史 ROS 应用残留污染 ROS graph；它不等于 motion/HIL/pass、Nav2 execution、真实路线
执行或 delivery success。

## 2026-06-11 13:25 Camera Visible Gate Live Probe

`sprints/2026.06.11_13-25_camera_visible_gate_live_probe/` 复核了真实上位机
camera visible content gate。本轮没有调用 `/api/base/manual`，没有发布 `/cmd_vel`，
没有打开或修改 `/dev/ttyS5`、`/dev/ttyACM0`，也没有改 WAVE ROVER、ESP32 或底盘
launch 配置。

采用资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_en/12/flask_camera.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/12/flask_camera.py`

真实上位机 readback：

- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/api/camera/health active_peer_count=0`
- `/api/camera/devices` 显示 `/dev/video0`、`/dev/video1`、`/dev/video2`。
- `v4l2-ctl --list-devices` 仍显示 `/dev/video1` 是 DV20 USB capture，
  `/dev/video2` 是 metadata，`/dev/video0` 是 Cedrus 编解码设备。

OpenCV 结论：

- `/dev/video1` 默认、`MJPG`、`YUYV` 和多分辨率均可读帧，但默认样本仍是黑场。
- temporary boosted controls 后仍不可见。
- temporary manual exposure 最亮样本为 `mean_luma=7.29296875`、`max_luma=59`、
  `nonblack_ratio_gt10=0.172783203125`，能看到极弱轮廓，但不足以作为 HIL/manual gate
  的可见内容证据。
- 结束时 camera controls 已恢复到原值，probe 进程无残留，`/dev/ttyS5` 与
  `/dev/ttyACM0` 的 `lsof/fuser` 无输出。

当前 gate 状态：

- `camera_device_opened=true`
- `camera_service_active=true`
- `visible_content_proven=false`
- `manual_motion_hil_gate=blocked`

下一步现场动作清单：

1. 检查镜头盖、保护膜、遮挡、摄像头朝向和是否对准纯暗面。
2. 将镜头对准有纹理的高对比目标，并打开强补光。
3. 如果 DV20 是采集卡，确认 HDMI/AV视频源已接入且源端不是黑屏。
4. 若 DV20 仍无法输出清晰内容，插入 known-good USB UVC camera 并确认新的 capture
   `/dev/video*` 节点。
5. 重跑本 sprint OpenCV stats；在 `visible_content_proven=true` 前，不得放行非 stop
   手动运动或 HIL movement gate。
