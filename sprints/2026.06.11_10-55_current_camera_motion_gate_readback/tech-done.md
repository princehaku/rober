# Current Camera Motion Gate Readback

## Sprint Type

sprint_type: micro

## 实际改动

- 新建本轮只读硬件复核 sprint：
  `sprints/2026.06.11_10-55_current_camera_motion_gate_readback/`。
- 保存真实上位机 Robot API readback artifact：
  - `artifacts/api/operator_report.json`
  - `artifacts/api/base_status.json`
  - `artifacts/api/base_feedback_latest.json`
  - `artifacts/api/camera_health.json`
  - `artifacts/api/camera_devices.json`
  - `artifacts/api/radar_status.json`
  - `artifacts/api/radar_scan_proof_latest.json`
- 保存真实上位机 SSH 只读状态 artifact：
  - `artifacts/ssh/remote_readonly_service_device_status.log`
  - `artifacts/ssh/remote_v4l2_readonly.log`
- 保存当前默认相机帧统计：
  - `artifacts/camera/default_frame_stats.json`
- 保存本轮 manual non-stop gate 判定：
  - `artifacts/manual_gate_decision.json`
- 同步更新 `docs/hardware/board_sensor_stack_smoke.md`，记录当前相机、PC/manual HIL gate、
  串口占用、服务状态和雷达 readback 的最新边界。

## 采用资料来源与边界

- 已阅读 `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER 底盘事实采用：
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- 采用边界：WAVE ROVER 上下位机链路是 UART UTF-8 newline-delimited JSON；
  vendor Raspberry Pi 参考串口为 `/dev/ttyAMA0` 或 `/dev/serial0`，波特率 `115200`。
  Orange Pi 现场设备路径必须以实测为准；本轮实板 Robot API readback 显示底盘口为
  `/dev/ttyS5 @ 115200`。
- 本轮不修改 vendor、firmware、onboard、PC UI 或硬件配置；不直接写 `/dev/ttyS5`。
  `/api/base/status` 的底盘 readback 由上位机 API 执行非运动 `T=130`，只用于确认
  `T=1001` 反馈可见，不构成 HIL 或运动准入。

## 真实 readback 结果

- `/api/operator/report`：`operator_report_status=ready_for_execution`，人工 preflight
  字段为 `operator_present=true`、`physical_clearance_confirmed=true`、
  `emergency_stop_ready=true`；但 structured HIL claims 仍为
  `visible_content_proven=false`、`external_video_recorded=false`、
  `wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`、
  `delivery_success=false`。
- `/api/base/status`：`port=/dev/ttyS5`、`baudrate=115200`、
  `write_control_available=true`、`pyserial_available=true`；
  非运动 `T=130` readback 观察到 `T=1001`，但顶层仍为
  `safe_to_control=false`、`primary_actions_enabled=false`、
  `sends_motion_commands=false`。
- `/api/base/feedback-samples/latest`：latest artifact 可加载但 freshness 为 stale；
  保持 `safe_to_control=false`、`hil_pass=false`、`sends_motion_commands=false`。
- `/api/camera/health`：`status=ready`，上次 WebRTC auto selection 仍选择
  `/dev/video1`，active peers 为 0。
- `/api/camera/devices`：`/dev/video0`、`/dev/video1`、`/dev/video2` 存在。
- `/api/radar/status`：`scan_status=fresh_scan_proof_observed`，但仍有
  `blocked_reasons=["scan_continuity_not_observed"]`，保持
  `safe_to_control=false`、`sends_motion_commands=false`。
- `/api/radar/scan-proof/latest`：latest proof 内 `/scan` once、scan hz、
  `/lidar/raw_packet` 和 TF 观察为 true，`scan_hz_average_rate_hz=12.482`；
  但这是 LiDAR proof artifact，不是运动或底盘 HIL。

## SSH 只读状态结果

- `trashbot-upper-robot-api.service=active`，主进程参数包含
  `--base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`。
- `trashbot-local-webrtc-camera.service` 为 active；`rober-lidar.service` 和
  `trashbot-lidar.service` 为 inactive。
- `lsof /dev/ttyS5 /dev/ttyACM0 /dev/video0 /dev/video1 /dev/video2` 无输出；
  `fuser -v` 对同一组设备也无占用输出。
- `ss` 显示 Robot API 在 `0.0.0.0:8787` 监听，camera service 在
  `0.0.0.0:8088` 监听。
- 进程列表仍有多组历史 `waypoint_manager`、`map_recorder`、`task_orchestrator`
  ROS 进程；本轮只读记录，不清理或重启。

## 相机当前默认帧

OpenCV 只读打开 `/dev/video1`，未修改任何 V4L2 controls，读取 5 帧后统计最后一帧：

- `ok=true`
- `width=640`
- `height=480`
- `mean_luma=0.00103515625`
- `std_luma=0.03215718740092308`
- `max_luma=1`
- `nonblack_ratio_gt20=0.0`
- `very_dark_ratio_lt10=1.0`
- `near_black=true`

结论：当前相机仍 near-black，`visible_content_proven=false` 不能翻转。

## Manual Non-Stop Gate 判定

本轮不满足 exactly one jog 入口条件，判定为 `not_attempted`：

- `safe_to_control=false`
- `primary_actions_enabled=false`
- `visible_content_proven=false`
- `external_video_recorded=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `physical_motion_lidar_delta_proven=false`
- `delivery_success=false`
- 雷达仍有 `scan_continuity_not_observed`

本轮没有执行任何非零运动；没有调用远端 `/api/base/manual`；没有发布 `/cmd_vel`；
没有直接写 `/dev/ttyS5`；没有执行 stop。

## 验证结果

```text
git diff --check
```

结果：2026-06-11T10:50:44+08:00 重跑通过，无输出。

## 剩余风险

- 相机物理输入仍近黑，需现场检查遮挡、保护膜、朝向、补光、DV20 输入源或更换已知可见
  USB UVC 摄像头。
- Robot API 可用 `T=130` 读到 `T=1001`，但 stale feedback samples、wheel feedback 非零、
  物理 LiDAR motion delta 和外部视频仍未证明。
- 当前有多组历史 ROS 进程残留；本轮按只读要求未清理，后续进入运动或 Nav2 前需要先做
  进程归一和清场确认。
- PC workstation 未在本机常规端口运行；`127.0.0.1:18789` 是 openclaw gateway，
  `/api/robot-control/summary` 返回 404。因此本轮 PC manual gate 以 Robot API readback
  和 operator report 判定，未通过 PC proxy 执行 stop 或 jog。
