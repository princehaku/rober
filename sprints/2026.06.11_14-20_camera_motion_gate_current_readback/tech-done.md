# 2026-06-11 14:20 Camera Motion Gate Current Readback

## Sprint Type

sprint_type: micro

## 本轮目标

复核真实上位机当前状态下的摄像头可见内容与运动 gate。该轮只允许
SSH/API readback、相机帧统计和清场检查；不执行 `/cmd_vel`、Nav2、
`/api/base/manual` 非 stop 或任何非零运动。

## 采用的 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

本轮采用的硬件事实：

- WAVE ROVER 上下位机链路是 UART，每行一个 UTF-8 JSON，以 `\n` 结尾。
- vendor Raspberry Pi 上位机默认串口是 `/dev/ttyAMA0 @ 115200`，不能外推到
  Orange Pi；Orange Pi 实板路径必须以目标机 readback 为准。
- 关键底盘命令边界：`T=1` 左右轮速度、`T=13` ROS 速度、
  `T=130` 底盘反馈请求、`T=131` 反馈流开关。

## 实际改动

- 新增本轮 sprint artifact：
  - `artifacts/api/camera_health.json`
  - `artifacts/api/camera_devices.json`
  - `artifacts/api/operator_report.json`
  - `artifacts/api/base_status.json`
  - `artifacts/api/radar_status.json`
  - `artifacts/api/base_feedback_samples_latest.json`
  - `artifacts/ssh/ssh_identity.log`
  - `artifacts/ssh/v4l2_list_devices_all.log`
  - `artifacts/camera/video1_frame_stats.json`
  - `artifacts/camera/video1_sample_capture.json`
  - `artifacts/camera/video1_sample.jpg`
  - `artifacts/cleanup/remote_device_process_cleanup_final.log`
  - `artifacts/manual_motion_gate_decision.json`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，追加本轮相机与 motion gate
  current readback 结论。

未修改 PC 源码、onboard 产品代码、launch、硬件配置或 vendor 文件。

## 真实 readback 结果

目标：

- Robot API：`http://192.168.1.11:8787`
- SSH：`root@192.168.1.11 -p 37878`

API readback 均返回 HTTP 200：

- `/api/camera/health`
- `/api/camera/devices`
- `/api/operator/report`
- `/api/base/status`
- `/api/radar/status`
- `/api/base/feedback-samples/latest`

摄像头设备事实：

- `/api/camera/devices` 与 `v4l2-ctl --list-devices --all` 均显示
  `USB Composite Device: DV20 USB` 对应 `/dev/video1`、`/dev/video2`。
- `/api/camera/health` 显示 camera service `status=ready`，上次选中的实际源为
  `/dev/video1`，`safe_to_control=false`，`robot_control_executed=false`。

当前帧统计：

```json
{
  "device": "/dev/video1",
  "opened": true,
  "frames_read": 12,
  "read_failures": 0,
  "frame_shape": [480, 640, 3],
  "gray_mean": 0.0010677083333333333,
  "gray_std": 0.0326583577702288,
  "gray_max": 1,
  "near_black_ratio_lt8": 1.0,
  "non_black_ratio_ge16": 0.0,
  "heuristic_visible_content": false,
  "heuristic_near_black": true
}
```

结论：真实 `/dev/video1` 设备可打开并可读帧，但当前帧仍是 near-black，不是
可用可见图传材料。样图已保存到 `artifacts/camera/video1_sample.jpg`。

运动 gate readback：

- `/api/base/status`：`/dev/ttyS5 @ 115200` 存在，非运动 `T=130` readback
  观察到 `T=1001`；`safe_to_control=false`、
  `sends_motion_commands=false`、`robot_control_executed=false`、
  `primary_actions_enabled=false`。
- `/api/base/feedback-samples/latest`：历史 latest samples 中 2/2 观察到
  `T=1001`，但 artifact freshness 为 stale；它只能说明非运动反馈材料存在，
  不能作为 HIL pass 或运动准入。
- `/api/radar/status`：`fresh_scan_proof_observed=true`，
  `scan_status=fresh_scan_proof_observed`，但 `continuous_scan_status=not_proven`，
  且 `safe_to_control=false`、`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`primary_actions_enabled=false`。
- `/api/operator/report`：`safe_to_control=false`、`hil_pass=false`、
  `delivery_success=false`、`visible_content_proven=false`、
  `wheel_feedback_lr_nonzero_proven=false`、
  `physical_motion_lidar_delta_proven=false`。

本轮生成 `artifacts/manual_motion_gate_decision.json`：

```json
{
  "manual_motion_gate_allowed": false,
  "nonzero_motion_allowed": false,
  "reason": "current /dev/video1 frame is still near-black and safety/HIL fields remain false; only stop/read-only confirmation is allowed"
}
```

## 验证结果

运行的真实上位机 readback 命令包括：

```bash
curl -sS --max-time 10 http://192.168.1.11:8787/api/camera/health
curl -sS --max-time 10 http://192.168.1.11:8787/api/camera/devices
curl -sS --max-time 10 http://192.168.1.11:8787/api/operator/report
curl -sS --max-time 10 http://192.168.1.11:8787/api/base/status
curl -sS --max-time 10 http://192.168.1.11:8787/api/radar/status
curl -sS --max-time 10 http://192.168.1.11:8787/api/base/feedback-samples/latest
ssh -p 37878 root@192.168.1.11 'v4l2-ctl --list-devices --all'
ssh -p 37878 root@192.168.1.11 'python3 ... cv2.VideoCapture("/dev/video1", cv2.CAP_V4L2) ...'
```

清场结果：

```text
2026-06-11T14:19:03+08:00
PS_RESIDUAL
LSOF_VIDEO_TTY
FUSER_VIDEO_TTY
```

`PS_RESIDUAL`、`LSOF_VIDEO_TTY`、`FUSER_VIDEO_TTY` 后均无条目，表示本轮采样
没有留下相机、`/dev/ttyS5` 或 `/dev/ttyACM0` 占用。

`git diff --check` 已运行，通过，无输出。

## 失败定位

相机不是设备枚举失败，也不是 OpenCV 打不开设备：`/dev/video1` 可打开，
12/12 帧读取成功。失败点是当前图像内容仍为 near-black：
`gray_mean=0.0011`、`gray_max=1`、`near_black_ratio_lt8=1.0`。

因此本轮不能把摄像头写成“可见内容已恢复”，也不能基于当前材料放开运动 gate。

## 剩余风险

- 未执行非零运动，这是本轮明确安全边界；真实运动 sprint 仍需另行派发。
- 当前相机问题可能来自镜头盖、遮挡、照明、UVC 曝光/格式、摄像头链路或物理安装，
  本轮只证明当前帧内容不可见，没有拆解根因。
- `/api/base/status` 会通过 API 发出非运动 `T=130` 反馈请求；本轮未直接写
  WAVE ROVER UART，且未发送 `T=1/T=13/T=131`。
- Radar fresh scan proof 存在，但 continuous scan 仍未证明，不能作为运动 HIL
  准入材料。

