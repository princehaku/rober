# Camera Visible Gate Live Probe

sprint_type: micro

## 本轮目标

在真实上位机 `root@192.168.1.11:37878` 上做一次非运动 live camera recovery/probe，
确认 DV20 `/dev/video1` 是否能产出足够清晰的可见内容，作为 PC 手动运动/HIL gate 的相机材料。
本轮不改 PC 普通用户首屏，不执行底盘运动，不触碰 WAVE ROVER 串口/运动控制配置。

## 已读资料来源

- `AGENTS.md`
  - 硬件相关任务必须先读 `docs/vendor/VENDOR_INDEX.md`，真实集成不得猜测设备、波特率、协议或硬件事实。
- `OKR.md`
  - 当前现场优先级是补真实上位机证据；PC/O7 仍缺真实 RTC/视频和上车验证。
- `docs/vendor/VENDOR_INDEX.md`
  - Orange Pi Zero 3 是项目主 SBC；WAVE ROVER vendor Raspberry Pi 参考不能直接当 Orange Pi 结论。
  - `ugv_rpi/config.yaml`、`cv_ctrl.py` 是 Waveshare 上位机 camera/CV 参考入口。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor 参考视频默认 `640x480`，`default_quality=20`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - vendor 参考 app 优先 USB camera，使用 `cv2.VideoCapture(0)`，再尝试 CSI/OAK。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_en/12/flask_camera.py`
  - vendor 教程展示 Picamera2 + OpenCV JPEG streaming，但这是 Raspberry Pi/CSI 参考，不证明 Orange Pi CSI。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/12/flask_camera.py`
  - 同上，中文教程额外做 `cv2.cvtColor`；本轮未引入 Picamera2 假设。

## 实际改动

- 新增本轮 artifacts：
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/00_ssh_tool_probe.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/01_systemd_camera_services.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/02_camera_api_health_devices.jsonl`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/03_v4l2_identity_formats_controls.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/04_process_device_baseline.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/05_opencv_probe_stdout.json`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/06_control_restore_readback.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/07_final_cleanup_readback.txt`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/remote/opencv_frame_stats.json`
  - `sprints/2026.06.11_13-25_camera_visible_gate_live_probe/artifacts/frames/*.jpg`
- 新增本文件，记录 micro sprint 结论、验证结果和剩余风险。
- 更新 `docs/vision/board_camera_publisher.md`，补充 2026-06-11 13:25 live probe 结论。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，把手动/HIL gate 的 camera blocker 更新为更具体的现场动作清单。

未修改：

- PC 普通用户首屏组件/样式。
- WAVE ROVER、ESP32、底盘串口、运动控制代码或配置。
- `docs/vendor/**`。
- factory firmware。

## 真实上位机验证结果

### 工具和服务

`ssh -p 37878 root@192.168.1.11` 成功；板端信息：

- 时间：`2026-06-11T13:22:02+08:00`
- 主机：`op-z3-b6.home`
- 内核：`Linux 6.1.31-sun50iw9 aarch64`
- `/usr/bin/v4l2-ctl` 存在
- `/usr/local/bin/ffmpeg` 存在
- OpenCV：`cv2 4.10.0`

`systemctl is-active trashbot-upper-robot-api.service trashbot-local-webrtc-camera.service`：

```text
active
active
```

`/api/camera/health`：

- `status=ready`
- `video_source=auto`
- `active_peer_count=0`
- `active_peer_connections=0`
- `safe_to_control=false`
- `robot_control_executed=false`
- last closed peer 选择过 `/dev/video1`，`frames_read=108`，`camera_read_failures=0`

`/api/camera/devices`：

- `/dev/video0`、`/dev/video1`、`/dev/video2` 均存在。
- `v4l2-ctl --list-devices` 显示：
  - `/dev/video0` 是 `cedrus (platform:cedrus)`。
  - `/dev/video1` 和 `/dev/video2` 属于 `USB Composite Device: DV20 USB`。

### V4L2 设备事实

`/dev/video1`：

- driver：`uvcvideo`
- card：`USB Composite Device: DV20 USB`
- capability：`Video Capture`
- formats：
  - `MJPG`：`1280x720`、`640x480`、`480x320`、`1920x1080`
  - `YUYV`：`640x480`、`320x240`
- controls 初始值：
  - `brightness=0`
  - `contrast=256`
  - `saturation=250`
  - `gamma=20`
  - `gain=4`
  - `power_line_frequency=0`
  - `white_balance_temperature=4500`
  - `sharpness=100`
  - `backlight_compensation=0`
  - `auto_exposure=3 (Aperture Priority Mode)`
  - `exposure_time_absolute=80`

`/dev/video2`：

- 同属 DV20，但 `Device Caps` 是 metadata capture，不是图像采集节点。

### OpenCV 单帧统计

核心 artifact：

- `artifacts/remote/opencv_frame_stats.json`
- 最亮样例：`artifacts/frames/video1_manual_exposure_mjpg_640x480.jpg`

默认和格式矩阵：

| 样本 | opened | read_ok | mean_luma | max_luma | nonblack_ratio_gt10 | near_black | visible_content_proven |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `video0_default` | false | false | - | - | - | - | - |
| `video1_default` | true | true | 0.0011458333 | 1 | 0.0 | true | false |
| `video1_mjpg_640x480` | true | true | 1.0 | 1 | 0.0 | true | false |
| `video1_yuyv_640x480` | true | true | 0.0008658854 | 1 | 0.0 | true | false |
| `video1_mjpg_1280x720` | true | true | 1.0 | 1 | 0.0 | true | false |
| `video1_mjpg_1920x1080` | true | true | 1.0 | 1 | 0.0 | true | false |
| `video1_yuyv_320x240` | true | true | 0.0013802083 | 1 | 0.0 | true | false |
| `video2_default` | false | false | - | - | - | - | - |
| `video1_boosted_controls_mjpg_640x480` | true | true | 1.0 | 1 | 0.0 | true | false |
| `video1_manual_exposure_mjpg_640x480` | true | true | 7.29296875 | 59 | 0.172783203125 | false | false |

临时 control recovery/probe：

- boost 组合：`brightness=127`、`contrast=511`、`saturation=511`、`gain=7`、
  `backlight_compensation=255`、`power_line_frequency=1`、`auto_exposure=3`。
- manual exposure 组合：`auto_exposure=1`、`exposure_time_absolute=100000`、
  `gain=7`、`brightness=127`、`backlight_compensation=255`。
- manual exposure 可以让极暗画面出现微弱轮廓，但仍不是稳定可见内容。
- 所有临时 controls 已恢复；最终 readback 为：
  - `brightness=0`
  - `contrast=256`
  - `saturation=250`
  - `gamma=20`
  - `gain=4`
  - `power_line_frequency=0`
  - `white_balance_temperature=4500`
  - `sharpness=100`
  - `backlight_compensation=0`
  - `auto_exposure=3 (Aperture Priority Mode)`
  - `exposure_time_absolute=80`

布尔结论：

- `camera_device_opened=true`
- `camera_service_active=true`
- `active_peers=0`
- `visible_content_proven=false`

### 清场结果

最终 readback：

- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- `/api/camera/health active_peer_count=0`
- probe 进程无残留。
- `fuser -v /dev/video0 /dev/video1 /dev/video2` 无输出。
- `lsof /dev/ttyS5 /dev/ttyACM0` 无输出。
- `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出。

本轮没有调用 `/api/base/manual`，没有发布 `/cmd_vel`，没有执行底盘运动。

## Blocker 和下一步现场动作

`visible_content_proven=false` 仍阻挡手动运动/HIL gate。更精确的 blocker 是：

- DV20 UVC capture 节点存在且能读帧，但默认、MJPG、YUYV、多分辨率输出均接近黑场。
- `/dev/video2` 不是 alternate capture 节点；`/dev/video0` 是 Cedrus 编解码设备，不是相机。
- manual exposure 只让极暗画面出现微弱轮廓，说明更像现场光路/输入源/光照问题，而不是 OpenCV 或 WebRTC 链路完全断开。

现场必须按顺序处理：

1. 检查镜头盖、保护膜、遮挡、摄像头朝向和是否对准纯暗面。
2. 把镜头对准有纹理的高对比目标，并打开强补光后重跑本 sprint OpenCV 统计。
3. 确认 DV20 是否实际为采集卡；如果是采集卡，确认 HDMI/AV视频源已接入且不是黑屏输出。
4. 若 DV20 仍黑，插入 known-good USB UVC camera，确认是否出现新的 `/dev/video*` capture 节点并重跑 `/api/camera/devices` 与 OpenCV stats。
5. 在 `visible_content_proven=true` 前，不允许把相机材料用于手动运动/HIL gate 放行。

## 剩余风险

- 本轮没有真实外部视角视频，也没有证明摄像头朝向；只能基于远端帧统计和样例图判断。
- OpenCV 可读帧不等于视觉可用；当前样例仍不足以支持路线关键帧、视觉定位、障碍识别或 HIL 放行。
- 远端服务代码未改动；如果现场更换摄像头导致枚举变化，需要重新确认 auto source 是否仍选中正确 capture 节点。

