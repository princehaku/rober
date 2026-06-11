# 2026-06-11 20:05 Camera Visible Content Gate Refresh

## sprint_type

micro

## owner

`robot-hardware-engineer`

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/12/flask_camera.py`

采用边界：

- vendor `config.yaml` 的视频默认尺寸是 `640x480`，vendor `cv_ctrl.py` 的 USB camera 分支使用 OpenCV `VideoCapture` 作为上位机相机入口。
- vendor `flask_camera.py` 证明 Waveshare 参考 app 有实时图传样例，但该样例偏 Raspberry Pi/Picamera2；本项目 Orange Pi Zero 3 现场事实仍以本轮 `/dev/video1` V4L2/OpenCV 读回为准。
- 本轮不采用 Raspberry Pi 串口、Picamera2 或 CSI 假设，不修改 `docs/vendor/**`。

## 安全边界

- camera-only；没有调用 `/api/base/manual`。
- 没有发布 `/cmd_vel`，没有执行 Nav2/NavigateToPose。
- 没有打开底盘 `/dev/ttyS5`；只通过 `lsof/fuser` 检查是否有占用。
- 没有修改 PC 普通首屏 UI、WAVE ROVER base driver、底盘串口配置、launch 硬件参数或 vendor 文件。

## 实际改动

- 新增 `sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/tech-done.md`
- 新增本轮 artifacts：
  - `sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/artifacts/api/`
  - `sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/artifacts/remote_capture/`
  - `sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/artifacts/cleanup/`
- 更新 `docs/vision/board_camera_publisher.md`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`
- 更新 `docs/hardware/field_hil_execution_pack.md`

## 真实上位机 readback

目标：

- SSH：`root@192.168.1.11 -p 37878`
- Robot API：`http://192.168.1.11:8787`

HTTP/API 读回：

- `/api/camera/health`：HTTP 200，`status=ready`，`active_peer_count=0`，`active_frames_read=0`，`active_camera_read_failures=0`，`safe_to_control=false`，`robot_control_executed=false`。
- `/api/camera/devices`：HTTP 200，`/dev/video0`、`/dev/video1`、`/dev/video2` 均存在且可读写；`v4l2-ctl --list-devices` 仍显示 `USB Composite Device: DV20 USB` 对应 `/dev/video1`/`/dev/video2`。
- `/api/operator/report` 初始读回：`visible_content_proven=false`，`camera_artifacts_ref=not_attached_no_motion_smoke`，`safe_to_control=false`，`primary_actions_enabled=false`。

SSH/service 读回：

- host：`op-z3-b6.home`
- `trashbot-upper-robot-api.service`：`active`
- `trashbot-local-webrtc-camera.service`：`active`
- `v4l2-ctl -d /dev/video1 --all`：driver `uvcvideo`，card `USB Composite Device: DV20 USB`，capability 包含 `Video Capture`。
- `/dev/video1` 支持格式保持为：
  - `MJPG`：`1280x720`、`640x480`、`480x320`、`1920x1080`
  - `YUYV`：`640x480`、`320x240`
- controls 当前保持原始值：`brightness=0`、`contrast=256`、`saturation=250`、`gamma=20`、`gain=4`、`auto_exposure=3`、`exposure_time_absolute=80 flags=inactive`。

## OpenCV direct probe 结果

本轮先启动了一版 12 次读帧脚本，但 V4L2 每次 `cap.read()` 阻塞约 10 秒并持续输出 `select() timeout`，为避免长时间占用 `/dev/video1`，已中止并清理残留远端 `python3` PID `289209`。清理后 `/dev/video0`、`/dev/video1`、`/dev/video2`、`/dev/ttyS5` 均无占用。

随后改用每档 14 秒上限的短超时 OpenCV probe。结果：

| 样本 | open_ok | read_ok | first_frame_timeout | 实际格式 | 实际分辨率 | visible_content_proven |
| --- | --- | --- | --- | --- | --- | --- |
| `default` | true | false | true | `YUYV` | `640x480 @ 22fps` | false |
| `mjpg_640x480` | true | false | true | `MJPG` | `640x480 @ 30fps` | false |
| `yuyv_640x480` | true | false | true | `YUYV` | `640x480 @ 22fps` | false |

结论：

- `visible_content_proven=false`
- 本轮失败类型是 `first-frame timeout`，不是“可见内容已经恢复”。
- 由于没有任何 `read_ok=true` 的 frame，本轮没有 sample JPG/PNG，也没有可见 frame 指标；每档 metrics JSON 只记录 open/read/timeout 状态。

关键 artifact：

- `artifacts/remote_capture/opencv_short_timeout_probe.log`
- `artifacts/remote_capture/opencv_short_timeout_probe_files/summary.json`
- `artifacts/remote_capture/opencv_short_timeout_probe_files/default.metrics.json`
- `artifacts/remote_capture/opencv_short_timeout_probe_files/mjpg_640x480.metrics.json`
- `artifacts/remote_capture/opencv_short_timeout_probe_files/yuyv_640x480.metrics.json`

## Operator report 更新

已通过 `POST /api/operator/report` 写入本轮 camera-only 失败材料：

- `evidence_ref=sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/artifacts/remote_capture/opencv_short_timeout_probe_files`
- `visible_content_proven=false`
- `site_state=camera_direct_first_frame_timeout`
- `external_video_recorded=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `physical_motion_lidar_delta_proven=false`
- `real_route_map_proven=false`
- `delivery_success=false`

读回仍保持安全字段：

- `operator_report_material_only=true`
- `report_replaces_stop_status_ack_or_hil=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `opens_serial=false`
- `publishes_cmd_vel=false`
- `robot_control_executed=false`
- `safe_to_control=false`
- `hil_pass=false`
- `primary_actions_enabled=false`

## PC/WebRTC 实时图传复核

未执行 offer/self-test。

原因：OpenCV direct `/dev/video1` 三档均 `open_ok=true` 但 `read_ok=false`、`first_frame_timeout=true`。底层 direct frame 尚不可用时，继续跑 PC/WebRTC 只能证明信令或服务状态，不能证明“实时图传能看到可见内容”。本轮只记录 `/api/camera/health` 的服务健康和 `active_peer_count=0`。

## cleanup/readback

最终清场：

- `/api/camera/health`：`status=ready`，`active_peer_count=0`
- `trashbot-upper-robot-api.service`：`active`
- `trashbot-local-webrtc-camera.service`：`active`
- `lsof/fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`：无输出
- 未见本轮采样进程残留。

清场 artifact：

- `artifacts/cleanup/camera_health_after.json`
- `artifacts/cleanup/operator_report_after.json`
- `artifacts/cleanup/final_remote_cleanup_readback.log`

## 验证结果

- 真实上位机 camera health/devices/operator report HTTP readback：通过，见 `artifacts/api/` 和 `artifacts/cleanup/`。
- SSH V4L2/OpenCV camera probe：完成；`/dev/video1` 可打开但 default、MJPG 640x480、YUYV 640x480 均 first-frame timeout。
- sample image：未生成，原因是没有任何 `read_ok=true` frame。
- metrics JSON：已保存三档 timeout metrics 与 summary。
- cleanup readback：通过；`active_peer_count=0`，服务 active，`/dev/video*` 与 `/dev/ttyS5` 无占用。
- `git diff --check -- sprints/2026.06.11_20-05_camera_visible_content_gate_refresh docs/vision/board_camera_publisher.md docs/hardware/board_sensor_stack_smoke.md docs/hardware/field_hil_execution_pack.md`：通过，无输出。

## 剩余风险和下一步现场动作

当前不应继续在软件侧扩大相机控制矩阵，也不应把 motion gate 放开。下一步必须压缩为现场硬件动作：

1. 现场确认 DV20 是 USB 摄像头还是采集卡；若是采集卡，确认 HDMI/AV 输入源已接入且源端不是黑屏或无信号。
2. 拆除镜头盖、保护膜和任何遮挡，确认镜头朝向不是机壳内壁、地面暗处或纯黑表面。
3. 将镜头对准高对比纹理目标并强补光，现场观察是否有图像变化。
4. 重新插拔 `/dev/video1` 对应 USB 设备，必要时换 USB 口、短线或供电更稳的 USB hub。
5. 用 known-good UVC USB 摄像头替换 DV20 后重跑本 sprint 的三档 OpenCV probe。
6. 若换 known-good UVC 后可见，才能继续 PC/WebRTC offer self-test 和非 stop motion gate 的上层复核。
