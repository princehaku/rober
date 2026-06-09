# LiDAR Motion Delta Retry

## sprint_type: micro

## 目标

在真实上位机 `root@192.168.1.11 -p 37878` 上，基于已聚合发布的 `/scan`
重试一次极低速短脉冲 motion-delta evidence capture，判断是否能证明真实物理运动。

本轮只允许在安全预检通过后发送一次 bounded `/cmd_vel`；`/odom` 仍按
command integration 记录，不能作为真实运动证据。

## 安全预检

- SSH 必须可达，远端 ROS Humble 与 `/root/rober/onboard/install/setup.bash`
  必须可 source，`ros2 pkg prefix ros2_trashbot_hardware` 必须可解析。
- 设备必须存在：LiDAR `/dev/ttyACM0`，WAVE ROVER UART `/dev/ttyS5`。
- 若 `trashbot-upper-robot-api.service` 占用 `/dev/ttyS5`，只允许在记录状态后临时停止；
  本轮结束必须恢复为 `active`。
- 最小 ROS stack 必须启动：`lidar_driver` 使用 `/dev/ttyACM0 @ 150000`，
  `esp32_bridge` 使用 `/dev/ttyS5 @ 115200 command_mode:=speed`。
- `/trashbot/stop` 必须可调用且返回 `success=True`；预停车失败时不得发送 `/cmd_vel`。
- `/scan` 聚合健康门槛：baseline 必须至少 3 帧，最新聚合帧
  `ranges_count >= 80`、`finite_count >= 80`、`angle_span_deg >= 90`。
- 清场检查必须确认本轮 `lidar_driver`、`esp32_bridge` 和 probe 进程无残留；
  若本轮停过 API 服务，必须恢复 `trashbot-upper-robot-api.service active`。

## 命令边界

- 只允许一次极低速短脉冲：`linear.x <= 0.03 m/s`，`angular.z = 0`，
  publish 窗口不超过 `0.25 s`。
- 脉冲后立即发布零速并调用 `/trashbot/stop`；脚本 `finally` 中再次发布零速并调用 stop。
- 不启动 Nav2、自主任务、相机或任何非必要节点。
- `motion_commands_sent` 必须真实记录；如果安全预检失败，该字段必须为 `false`。

## 验收阈值

- `physical_motion_lidar_delta_proven=true` 只在同时满足以下保守阈值时成立：
  - `paired_bins >= 40`
  - `median_abs_diff_m >= 0.03`
  - `changed_bin_ratio >= 0.12`
  - baseline/post 的聚合 `/scan` 都满足 `ranges_count >= 80`、`finite_count >= 80`、
    `angle_span_deg >= 90`
- `wheel_feedback_lr_nonzero_proven=true` 只在本轮 WAVE ROVER `T=1001` debug log
  中观测到任一 post/motion 帧 `abs(left_speed) > 0` 或 `abs(right_speed) > 0` 时成立。
- `safe_to_control=true` 只在 stop 可用、清场成功、服务恢复成功，且没有异常串口占用时成立；
  它不等价于可自主发车。
- `delivery_success=true` 本轮预计保持 `false`；本轮不是送达任务。

## 清场检查

- 停止本轮启动的 ROS 进程。
- 补发 `/trashbot/stop` 或等价零速 UART 停车。
- 检查 `/dev/ttyS5`、`/dev/ttyACM0` 占用。
- 恢复并检查 `trashbot-upper-robot-api.service`。

## 已读资料来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py`

## 采用的硬件事实

- WAVE ROVER 上下位机链路是 UART newline-delimited UTF-8 JSON。
- vendor RPi 默认底盘串口是 `/dev/ttyAMA0 @ 115200`；本项目 Orange Pi 实板
  必须以现场设备为准，本轮使用上一轮已证实的 `/dev/ttyS5 @ 115200`。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`。
- `json_cmd.h` 定义 `CMD_ROS_CTRL=13`，但本项目当前实测仍使用 `command_mode:=speed`
  的 `T=1` 差速速度命令。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、
  `CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143`、
  `FEEDBACK_BASE_INFO=1001`。
- 当前 `esp32_bridge` 的 `/trashbot/stop` 通过 `{"T":1,"L":0,"R":0}` 停车；
  `/odom` 是 ROS-side command integration，不是实测里程计。

## 实际改动

- 新增 `sprints/2026.06.10_03-45_lidar_motion_delta_retry/artifacts/lidar_motion_delta_retry_probe.py`
  - 订阅 `/scan`、`/odom`、`/battery`、`/imu/data`。
  - 调用 `/trashbot/stop` 做预停车，baseline `/scan` 健康检查通过后才发送一次 bounded `/cmd_vel`。
  - 脉冲后发布零速并再次调用 `/trashbot/stop`，输出 JSON/CSV/JSONL artifacts。
- 新增并拉回远端 artifacts：`sprints/2026.06.10_03-45_lidar_motion_delta_retry/artifacts/remote_capture/`
  - `01_connection_workspace.log`
  - `02_precheck_devices_service.log`
  - `05_stack_topics_services.log`
  - `06_stop_precheck.log`
  - `07_scan_echo_once.log`
  - `08_probe_stdout.log`
  - `lidar_motion_delta_retry_summary.json`
  - `scan_delta_metrics.csv`
  - `scan_frame_stats.jsonl`
  - `wave_rover_feedback_debug.jsonl`
  - `feedback_lr_summary_after_cleanup_copy.json`
  - `final_cleanup_check.log`
  - `final_cleanup_rerun.log`
  - `final_strict_remote_check.log`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，追加本轮聚合 `/scan`
  motion-delta retry 结论与风险边界。
- 未修改产品代码、launch、底盘控制逻辑、LiDAR driver、camera 代码或固件。

## 验证结果

### 1. SSH 连接与 ROS 工作区

命令已执行：

```text
$ ssh root@192.168.1.11 -p 37878 'echo connected && hostname && date'
connected
op-z3-b6.home
Wed Jun 10 03:39:35 AM CST 2026
```

远端工作区检查通过：

```text
connected
op-z3-b6.home
Wed Jun 10 03:42:04 AM CST 2026
ROS_DISTRO=humble
/root/rober/onboard/install/ros2_trashbot_hardware
```

设备检查：

```text
crw-rw---- 1 root dialout 166,  0 Jun 10 03:41 /dev/ttyACM0
crw-rw---- 1 root dialout   4, 69 Jun 10 03:08 /dev/ttyS5
```

### 2. 安全预检

- 首次检查发现一个本轮之前遗留的 `lidar_driver` 占用 `/dev/ttyACM0`
  （PID `92060`），未发送运动命令，先按 PID 清理。
- `trashbot-upper-robot-api.service` 预检时为 `active`，但未占用 `/dev/ttyS5`；
  为避免串口竞争，本轮 capture 期间临时停止，结束后恢复。
- 本轮最小 stack 启动成功：

```text
[lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
[esp32_bridge]: Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200
[esp32_bridge]: ESP32Bridge ready: ... command_mode=speed; publish_odom_tf=True;
feedback_debug_log_enabled=True; odom source=ROS-side command integration until measured wheel odometry is validated
```

- `/trashbot/stop` 可用并返回成功：

```text
std_srvs.srv.Trigger_Response(success=True, message='Motors stopped')
```

- baseline `/scan` 健康检查通过：

```json
{
  "ranges_count": 183,
  "finite_count": 183,
  "angle_span_deg": 178.51561877965767
}
```

### 3. Motion pulse 与 stop

本轮已发送运动命令：

```json
{
  "motion_commands_sent": true,
  "pulse_linear_x_mps": 0.03,
  "pulse_angular_z_radps": 0.0,
  "actual_pulse_duration_s": 0.23607158900995273,
  "pre_stop": {"success": true, "message": "Motors stopped"},
  "post_stop": {"success": true, "message": "Motors stopped"},
  "stop_confirmed": true
}
```

`actual_pulse_duration_s=0.23607158900995273` 小于 `0.25s` 上限，
`linear.x=0.03` 未超过本轮上限，`angular.z=0`。

### 4. LiDAR delta 指标

artifact：`artifacts/remote_capture/lidar_motion_delta_retry_summary.json`

```json
{
  "scan_frames_baseline": 25,
  "scan_frames_post": 39,
  "paired_bins": 361,
  "median_abs_diff_m": 0.003999948501586914,
  "mean_abs_diff_m": 0.13545810067484418,
  "max_abs_diff_m": 5.6717500407248735,
  "changed_bin_ratio": 0.09418282548476455,
  "physical_motion_lidar_delta_proven": false,
  "failure_reason": "scan_delta_below_conservative_threshold"
}
```

补充统计：`scan_frame_stats.jsonl` 共 74 帧；post 39 帧中 30 帧满足
`ranges_count>=80`、`finite_count>=80`、`angle_span_deg>=90`。但 summary
记录的最后一帧 post 聚合为 `ranges_count=2`、`finite_count=2`，未满足
本轮“post 最新聚合帧也健康”的保守门槛；同时 `median_abs_diff_m` 与
`changed_bin_ratio` 也低于阈值。

### 5. `/odom` 与 wheel feedback

`/odom`：

```text
command_integration_odom_delta_m=0.00749907216
odom_source=ROS-side command integration; not measured wheel odometry
```

该位移只能说明 bridge 收到并积分了命令，不能写成真实物理运动。

WAVE ROVER `T=1001` debug log：

```json
{
  "feedback_records_after_cleanup_copy": 348,
  "wheel_feedback_lr_nonzero_proven": false,
  "nonzero_count": 0,
  "first_nonzero": null
}
```

本轮电池反馈存在，末尾电压样本约 `12.37572956V`；`left_speed/right_speed`
在拉回的 348 条记录中均为 `0.0`。

### 6. 清场检查

第一次 cleanup trap 只杀掉了 `ros2 run` wrapper PID，实际 child executable
仍短暂残留并占用 `/dev/ttyACM0` 与 `/dev/ttyS5`。已立即补跑
`final_cleanup_rerun.log`，最终状态：

```text
[after]
[after lsof]
[service]
active
trashbot-upper-robot-api.service ... Active: active (running)
```

补清场后，本轮 `lidar_driver`、`esp32_bridge`、probe 进程无残留；
`final_strict_remote_check.log` 中严格进程过滤无输出，`lsof /dev/ttyS5 /dev/ttyACM0`
无输出；`trashbot-upper-robot-api.service` 恢复 `active`。

## 结论布尔值

- `motion_commands_sent`: `true`
  - 理由：`linear.x=0.03`、`angular.z=0`、实际窗口
    `0.23607158900995273s`，脉冲前后 `/trashbot/stop` 均成功。
- `physical_motion_lidar_delta_proven`: `false`
  - 理由：`paired_bins=361` 足够，但 `median_abs_diff_m=0.0039999485`
    低于 `0.03` 阈值，`changed_bin_ratio=0.09418` 低于 `0.12` 阈值；
    最后一帧 post 聚合也退化为 2 点，不满足保守 post 健康门槛。
- `wheel_feedback_lr_nonzero_proven`: `false`
  - 理由：拉回后的 348 条 `T=1001` debug 记录中
    `left_speed/right_speed` 未出现非零。
- `safe_to_control`: `true`（仅限本轮同等 bounded 低速 smoke 条件）
  - 理由：stop service 可用，运动命令受限，补清场后串口无异常占用，
    API 服务恢复 active。该结论不等于 Nav2/autonomous 可发车。
- `delivery_success`: `false`
  - 理由：本轮不是送达任务，也未证明真实物理运动。

## 失败定位

- 物理运动没有被 LiDAR delta 证明。核心失败点不是 paired bins 数量，
  而是距离变化中位数和变化比例低于阈值。
- WAVE ROVER `T=1001.L/R` 仍不提供非零轮速反馈；不能把 wheel feedback
  写成真实运动证据。
- `/odom` 出现约 `0.0075m` 位移，但它来自 ROS-side command integration，
  只能证明命令积分路径，不能证明底盘实际移动。
- capture cleanup 脚本第一次只杀 wrapper PID，已经通过
  `final_cleanup_rerun.log` 修正并完成清场；后续远端脚本应直接按 child
  executable pattern 清理。

## 剩余风险

- 仍缺能证明真实 physical motion 的 LiDAR/camera/外部观测证据。
- 仍缺 WAVE ROVER 真实轮速或编码器反馈非零证据，`/odom` 继续不能当实测里程计。
- LiDAR 聚合发布已经显著改善覆盖，但偶发 post 帧可能退化为极少点；
  下次 motion-delta 应按“多帧健康 post profile”判定，而不是只看最后一帧。
- 本轮只证明极低速短脉冲控制链可在可停条件下执行；不提升到自主导航、
  送达闭环或 HIL 准入完成。
