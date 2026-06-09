# LiDAR Motion Delta Probe Tech Done

## sprint_type: micro

## 目标

在真实上位机上使用 LiDAR `/scan` 做一次低速短脉冲前/中/后变化分析，尝试补充一条不依赖 encoder、不依赖相机画面的物理运动佐证。

本轮只验证 LiDAR delta 是否足以支持“真实物理运动发生过”。若 scan 变化不足，必须如实写成未证明；不得用 `/odom` command integration 外推真实运动。

## 资料来源

已读资料：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/tech-done.md`
- `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/tech-done.md`

采用的 vendor 事实：

- `json_cmd.h`：`CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`；`CMD_BASE_FEEDBACK=130`；`CMD_BASE_FEEDBACK_FLOW=131`；`CMD_FEEDBACK_FLOW_INTERVAL=142`；`CMD_UART_ECHO_MODE=143`；`FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h`：`T=1` 进入 `setGoalSpeed(L,R)`，并刷新 `lastCmdRecvTime`；`T=130` 调用 `baseInfoFeedback()`；`T=131` 控制 feedback flow；串口按换行 JSON 解析。
- `ugv_rpi/base_ctrl.py`：上位机参考实现使用 `json.dumps(data) + '\n'` 写 UART；`base_speed_ctrl()` 发送 `{"T":1,"L":input_left,"R":input_right}`；vendor RPi 默认 `/dev/ttyAMA0 @115200`，本项目 Orange Pi 实板使用本轮现场确认的 `/dev/ttyS5 @115200`。
- 上一轮 wheel feedback sweep：`T=1` 低速和 `T=11` PWM sweep 下 `T=1001.L/R` 仍全零，因此本轮 `wheel_feedback_lr_nonzero_proven=false`。

## 实际改动

新增：

- `sprints/2026.06.10_03-10_lidar_motion_delta_probe/tools/lidar_motion_delta_probe.py`
  - ROS2 probe 脚本，订阅 `/scan`、`/odom`、`/tf`、`/battery`、`/imu/data`。
  - 先调用 `/trashbot/stop`，采集 baseline，再发送一次 bounded `/cmd_vel`：`linear.x=0.03`，窗口 `<=0.25s`，然后发布零速并再次调用 `/trashbot/stop`。
  - 生成 `lidar_motion_delta_summary.json`、`scan_frame_stats.jsonl`、`scan_delta_metrics.csv`。

新增 artifacts：

- `artifacts/lidar_motion_delta_summary.json`
- `artifacts/scan_delta_metrics.csv`
- `artifacts/scan_frame_stats.jsonl`
- `artifacts/remote_capture/*.log|*.txt|*.json|*.jsonl`

同步文档：

- `docs/hardware/board_sensor_stack_smoke.md`
  - 追加 2026-06-10 LiDAR motion delta probe 结论：本轮未证明物理运动，`/odom` 仍按 command integration 边界处理。

未修改产品代码、launch、驱动、固件或长期远端配置。

## 远端执行与安全边界

远端：

- SSH：`root@192.168.1.11 -p 37878`
- Host：`op-z3-b6.home`
- ROS：Humble，workspace `/root/rober/onboard`
- 设备：
  - `/dev/ttyS5`
  - `/dev/ttyACM0`

最小 stack：

```text
ros2_trashbot_hardware lidar_driver
  serial_port:=/dev/ttyACM0
  serial_baudrate:=150000

ros2_trashbot_hardware esp32_bridge
  serial_port:=/dev/ttyS5
  serial_baudrate:=115200
  command_mode:=speed
  feedback_interval_ms:=100
  publish_odom_tf:=true
```

安全边界：

- camera 未启动。
- Nav2/autonomous navigation 未启动。
- 脉冲上限：`max_linear_x_mps=0.03`，`max_pulse_duration_s=0.22162205299537163`。
- stop：
  - API 预停车 `{"T":1,"L":0,"R":0}` 成功写入。
  - `/trashbot/stop` 在 capture 前、capture 后、脚本 finally、补清场时均返回成功。
- 清场：
  - 第一次 cleanup 日志显示本轮 ROS 进程仍残留，已立即补跑 `final_cleanup_rerun.log`。
  - 最终只剩 `upper_robot_api.py`，`lsof /dev/ttyS5 /dev/ttyACM0` 为空，`trashbot-upper-robot-api.service` 为 `active`。
  - 恢复后的 API status fresh `T=1001` readback 可用。

## 验证结果

SSH/设备/source：

```text
HOST=op-z3-b6.home
Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64
/dev/ttyACM0 exists
/dev/ttyS5 exists
WORKSPACE=/root/rober/onboard
ROS_DISTRO=humble
/root/rober/onboard/install/ros2_trashbot_hardware
```

vendor grep 摘要：

```text
json_cmd.h:
FEEDBACK_BASE_INFO 1001
CMD_SPEED_CTRL 1
CMD_BASE_FEEDBACK 130
CMD_BASE_FEEDBACK_FLOW 131
CMD_FEEDBACK_FLOW_INTERVAL 142
CMD_UART_ECHO_MODE 143

uart_ctrl.h:
case CMD_SPEED_CTRL -> setGoalSpeed(L,R)
case CMD_BASE_FEEDBACK -> baseInfoFeedback()
case CMD_BASE_FEEDBACK_FLOW -> setBaseInfoFeedbackMode(cmd)
serialCtrl() reads JSON until '\n'

base_ctrl.py:
send_command() writes json.dumps(data) + '\n'
base_speed_ctrl() sends {"T":1,"L":input_left,"R":input_right}
```

stack 启动日志：

```text
[lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
[esp32_bridge]: Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200
[esp32_bridge]: ESP32Bridge ready: ... command_mode=speed; publish_odom_tf=True; feedback_debug_log_enabled=True; odom source=ROS-side command integration until measured wheel odometry is validated
```

ROS topic/service：

```text
/battery
/cmd_vel
/imu/data
/odom
/scan
/tf
/trashbot/stop
```

scan 首帧：

```text
frame_id: laser_frame
angle_min: 1.9692223072052002
angle_max: 2.091395378112793
range_min: 0.05000000074505806
range_max: 8.0
ranges: [5.859000205993652, 0.6690000295639038, ...]
```

stop service：

```text
std_srvs.srv.Trigger_Response(success=True, message='Motors stopped')
```

summary 核心结果：

```json
{
  "motion_commands_sent": true,
  "max_pulse_duration_s": 0.22162205299537163,
  "max_linear_x_mps": 0.03,
  "stop_confirmed": true,
  "scan_frames_before": 896,
  "scan_frames_motion": 62,
  "scan_frames_after": 1194,
  "command_integration_odom_delta_m": 0.00601554609,
  "physical_motion_lidar_delta_proven": false,
  "wheel_feedback_lr_nonzero_proven": false,
  "safe_to_control": false,
  "delivery_success": false,
  "failure_reason": "scan_delta_below_conservative_threshold"
}
```

LiDAR delta：

```json
{
  "paired_bins": 1,
  "median_abs_diff_m": 0.006499767303466797,
  "max_abs_diff_m": 0.006499767303466797,
  "changed_bin_ratio": 0.0,
  "threshold": {
    "min_paired_bins": 40,
    "median_abs_diff_m_gte": 0.04,
    "changed_bin_ratio_gte": 0.18,
    "changed_bin_abs_threshold_m": 0.08
  }
}
```

本地验收命令：

```text
$ python3 -m json.tool sprints/2026.06.10_03-10_lidar_motion_delta_probe/artifacts/lidar_motion_delta_summary.json >/tmp/lidar_motion_delta_summary.check
pass

$ python3 - <<'PY' ...
physical_motion_lidar_delta_proven= False
command_integration_odom_delta_m= 0.00601554609
failure_reason= scan_delta_below_conservative_threshold
PY
```

最终清场：

```text
[final] process check
87738 python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 ...
[final] lsof
[final] service
active
```

恢复后 API：

```text
port=/dev/ttyS5
baudrate=115200
feedback_ack.t1001_observed=true
source=fresh_readback
safe_to_control=false
delivery_success=false
```

## 硬件结论

- 已证实：真实上位机可启动最小 ROS2 stack，`/scan`、`/odom`、`/tf`、`/battery`、`/imu/data` 和 `/trashbot/stop` 可观测。
- 已证实：本轮确实发送了 bounded `/cmd_vel` 脉冲，且速度/时长满足安全上限。
- 已证实：`/trashbot/stop` 成功，结束后 API 服务恢复，最终没有本轮 ROS 进程残留占用 `/dev/ttyS5` 或 `/dev/ttyACM0`。
- 未证实：LiDAR delta 不足以证明真实物理运动。`physical_motion_lidar_delta_proven=false`。
- 未证实：wheel feedback 非零。沿用上一轮事实，`wheel_feedback_lr_nonzero_proven=false`。
- `/odom` 非零只代表 ROS-side command integration，不能升级为实测里程计或物理运动证据。

## 失败定位

LiDAR 变化未通过保守阈值，主要原因：

- baseline/post 有足够帧数，但当前 `/scan` 每帧有限点较少，阶段聚合后可比 `paired_bins=1`，低于 `min_paired_bins=40`。
- baseline/post 的 `median_abs_diff_m=0.006499767303466797`，低于 `0.04m` 阈值。
- `changed_bin_ratio=0.0`，低于 `0.18` 阈值。
- motion 窗口内 `/odom` command integration 有 `0.00601554609m`，但这不是独立传感器证明。

## 剩余风险和下一步

- 当前 LiDAR driver 输出的 scan 扇区/点数不足以作为该低速短脉冲的稳定物理运动判据；需先确认 LiDAR 驱动是否应发布完整 360 profile，或改用更适合短距离的外部观察证据。
- 仍缺现场可视化轮子/底盘位移证据；不能区分“电机未实际转动”和“转动但 LiDAR 环境变化不足”。
- `T=1001.L/R` 仍未证明可用，真实 `/odom` 仍不能依赖 wheel feedback。
- 后续若继续做物理运动证明，建议使用现场视频/轮上标记/外部尺量或完整 scan profile，再与 `/cmd_vel`、`/odom`、`T=1001` 同步采集。
