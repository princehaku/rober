# 2026.07.04 07:38 PC live validation + camera zero-frame recovery

## sprint_type

micro

## 实际改动

- 本轮没有改产品代码；做了真实 PC 7001 与上位机 7878 的运行态复验，并同步文档。
- `docs/product/pc_tools_workstation.md`
  - 追加 07:38 现场验证：PC 大地图、WASD、相机直接采帧与 USB recovery 的当前事实。
- `docs/product/pc_free_roam_mapping_design.md`
  - 追加建图/自由移动边界：相机 0 帧只阻塞图传和建图视觉验收，不阻塞低速自由移动/WASD。
- `docs/process/okr_progress_log.md`
  - 追加 O7 进度日志，明确本轮不提升真实视频完成度，不宣称 wheel raw 或 delivery success。

## 验证结果

- 本地 PC 服务：
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `*:7001`。
- 上位机服务：
  - `ssh -p 7878 root@192.168.1.11` 可连。
  - `trashbot-upper-robot-api.service`、`trashbot-local-webrtc-camera.service`、`trashbot-esp32-bridge.service`、`trashbot-lidar-lifecycle.service` 均为 `active`。
- 地图：
  - `GET /api/robot-control/map/preview` 返回 `map_png_present=true`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`。
  - 雷达 proof 刷新后 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=6`，live-summary 返回 `radar_map_points_visible=true`。
- WASD / 手控链路：
  - 通过 PC 固定 `/api/robot-control/base/manual` 发 `forward/backward`，`speed_mps=0.08`、`duration_ms=500`。
  - 两次均返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
  - 补发固定 `/api/robot-control/base/stop` 后，live-summary 返回 `keyboard_motion_evidence_complete=true`、`keyboard_stop_settled_after_pulse=true`。
- 相机：
  - `/dev/video1` 是 DV20 UVC capture，`/dev/video2` 是 metadata；USB 为 `480M`，CMA 为 `cma_available_no_recent_failure`，无 owner 独占。
  - 停止 `trashbot-local-webrtc-camera.service` 后直接采帧：
    - `v4l2-ctl`：`MJPG 640x480`、`MJPG 480x320`、`MJPG 1280x720`、`MJPG 1920x1080`、`YUYV 320x240`、`YUYV 640x480` 全部 0 字节。
    - `ffmpeg`：`mjpeg 640x480` 无法在 EOF 前确定帧格式；`yuyv 320x240` 输出 0 帧。
    - 长窗口 `--stream-skip=5 --stream-count=3` 对 `MJPG 1920x1080`、`MJPG 640x480`、`YUYV 320x240` 仍为 0 字节。
  - PC 共享 MJPEG 返回 `first_frame_total_timeout`；PC status 返回 `source_first_frame_failed`、`uvc_no_frame_not_exclusive`、`camera_usb_speed=480M`。
  - 固定 `POST /api/robot-control/camera/usb-recovery` 返回 `status=streamon_failed`、`frame_observed=false`、`stream_failure_class=high_speed_zero_byte_no_frame`、`uvc_quirks_before=0`、`uvc_quirks_after=0`。

## 剩余风险

- 实时图传仍未完成：DV20 设备能枚举、能打开、无人独占、USB/CMA 正常，但不输出任何视频 buffer。下一步必须现场检查 DV20 上游输入、视频线、供电、接口、摄像头/采集卡本体，或换 known-good UVC 复测。
- wheel raw `T=1001 L/R` 仍为 `0/0`，本轮只证明 PC/WASD 命令链路、stop 和 IMU 动作信号，不证明 wheel raw 非零闭环。
- delivery success 和完整自动驾驶交付仍未完成，本轮不能上调为完成。
