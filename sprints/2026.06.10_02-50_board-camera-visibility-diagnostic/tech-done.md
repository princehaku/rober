# Board Camera Visibility Diagnostic Micro Sprint

- sprint_type: micro
- owner: robot-algorithm-engineer
- time: 2026-06-10 02:50 Asia/Shanghai
- motion_commands_sent=false
- safe_to_control=false
- delivery_success=false
- visible_content_proven=false

## 自主能力目标和本轮抓手

目标是通过真实上位机 SSH 做摄像头可见性诊断，补足上一轮关键帧几乎全黑的证据缺口。本轮只做相机设备枚举、V4L2 格式/控制项读取、单帧采样、亮度指标和临时曝光/亮度探测；没有执行底盘运动控制、没有发送 `/cmd_vel`，也没有修改产品代码或持久化硬件配置。

资料来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- 上车命令输出：`artifacts/ssh_host_info.log`、`artifacts/v4l2_enumeration.log`、`artifacts/remote_capture_session.log`、`artifacts/remote_control_restore.log`

本轮采用的硬件事实边界来自 `docs/vendor/VENDOR_INDEX.md`：主控为 Orange Pi Zero 3，底盘为 Waveshare WAVE ROVER，下位机为 ESP32；本轮不新增引脚、电压、UART、底盘协议或速度映射假设。

## 实际改动

新增本 sprint 内证据和一次性分析脚本：

- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/scripts/analyze_camera_visibility.py`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/ssh_host_info.log`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/v4l2_enumeration.log`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/remote_capture_session.log`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/remote_control_restore.log`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/remote_camera_capture.tgz`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/remote_capture/*.jpg`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_summary.json`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_samples.csv`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_contact_sheet.jpg`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_analysis.log`
- `sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/tech-done.md`

未修改产品代码、launch、驱动、测试或其它 sprint 目录。

## 接口影响

无 ROS2 接口影响。没有改动消息、action、launch 参数、硬件桥、Nav2 配置、相机驱动配置或行为状态机。远端仅使用 `/tmp/rober_camera_visibility_1781030663` 存放临时采样文件，并已将 `/dev/video1` 控制项显式恢复到默认/名义值。

## 实现内容

- SSH 到 `root@192.168.1.11 -p 37878`，记录主机、时间、内核、用户、`/dev/video*` 和工具可用性。
- 使用 `v4l2-ctl --list-devices`、`v4l2-ctl --all`、`v4l2-ctl --list-formats-ext`、`v4l2-ctl --list-ctrls` 枚举 `/dev/video0`、`/dev/video1`、`/dev/video2`。
- 确认 `/dev/video0` 是 Cedrus video decoder，不是相机采集节点；`/dev/video1` 是 UVC 相机 `USB Composite Device: DV20 USB`；`/dev/video2` 是 UVC metadata capture 节点。
- 用 `ffmpeg` 从 `/dev/video1` 采集 4 张 640x480 单帧：默认 MJPG、默认 YUYV、临时提高 brightness/gain/backlight 的 MJPG、临时手动曝光 MJPG。
- 临时探测后显式恢复：`brightness=0`、`gain=4`、`backlight_compensation=0`、`auto_exposure=3`、`exposure_time_absolute=80`。
- 本地脚本用 macOS `sips` 解码 JPEG，计算 mean/min/max luma、非黑像素比例、亮像素比例、动态范围和标准差；生成 JSON/CSV/contact sheet。
- 可见内容判据同时要求亮度和纹理/动态范围，避免把均匀灰/白帧误判为可用环境内容。

## 验证结果

SSH 连通/主机信息：

```text
== host ==
op-z3-b6.home
2026-06-10T02:43:49+08:00
Linux op-z3-b6.home 6.1.31-sun50iw9 #1.0.4 SMP Thu Jul 11 16:37:41 CST 2024 aarch64 ...
== video devices ==
/dev/video0
/dev/video1
/dev/video2
== tools ==
v4l2-ctl=/usr/bin/v4l2-ctl
ffmpeg=/usr/local/bin/ffmpeg
fswebcam=MISSING
python3=/usr/bin/python3
ros2=MISSING
```

V4L2 枚举关键输出：

```text
cedrus (platform:cedrus):
        /dev/video0
USB Composite Device: DV20 USB  (usb-5310000.usb-1):
        /dev/video1
        /dev/video2

/dev/video1 Driver name: uvcvideo
/dev/video1 Pixel Format: 'YUYV' 640/480
/dev/video1 formats: MJPG 1280x720/640x480/480x320/1920x1080 @30fps; YUYV 640x480 @22fps
/dev/video1 controls: brightness, contrast, saturation, gamma, gain, backlight_compensation, auto_exposure, exposure_time_absolute
```

采样命令结果：

```text
capture_rc_default_mjpg_640x480=0
capture_rc_default_yuyv_640x480=0
capture_rc_boosted_auto_mjpg_640x480=0
capture_rc_manual_exposure_mjpg_640x480=0
```

控制项恢复结果：

```text
brightness: 0
gain: 4
backlight_compensation: 0
auto_exposure: 3 (Aperture Priority Mode)
exposure_time_absolute: 80
```

亮度分析命令：

```bash
python3 sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/scripts/analyze_camera_visibility.py
```

关键输出：

```text
sample_count=4
best_sample_mean_luma=100.0
best_sample_non_black_ratio=1.0
best_sample_mostly_dark=false
visible_content_proven=false
```

JSON 格式检查：

```bash
python3 -m json.tool sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_summary.json >/tmp/camera_visibility_summary.check
```

关键输出：

```text
7362 /tmp/camera_visibility_summary.check
"schema": "trashbot.camera_visibility_diagnostic.v1"
```

summary 自检：

```text
camera_device= /dev/video1
sample_count= 4
best_sample_mean_luma= 100.0
best_sample_non_black_ratio= 1.0
best_sample_mostly_dark= False
best_sample_dynamic_range_luma= 0.0
visible_content_proven= False
manual_review_uniform_panels= True
manual_review_texture_visible= False
claim_boundary= 采样链路成功；默认样本黑场，调亮/手动曝光样本均匀灰/白且动态范围不足，因此 visible_content_proven=false；不能证明可用环境视觉内容。
motion_commands_sent= False
safe_to_control= False
delivery_success= False
```

文件清单命令：

```bash
find sprints/2026.06.10_02-50_board-camera-visibility-diagnostic -maxdepth 3 -type f | sort
```

关键输出包含：

```text
artifacts/camera_visibility_summary.json
artifacts/camera_visibility_samples.csv
artifacts/camera_visibility_contact_sheet.jpg
artifacts/remote_capture/default_mjpg_640x480.jpg
artifacts/remote_capture/default_yuyv_640x480.jpg
artifacts/remote_capture/boosted_auto_mjpg_640x480.jpg
artifacts/remote_capture/manual_exposure_mjpg_640x480.jpg
scripts/analyze_camera_visibility.py
tech-done.md
```

`git status --short`：

```text
?? sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/
```

## 数据、样本或调试输出变化

亮度指标：

```text
manual_exposure_mjpg_640x480: mean=100.0, min=100.0, max=100.0, dynamic_range=0.0, mostly_dark=false, visible_content_candidate=false
boosted_auto_mjpg_640x480: mean=80.0125, min=80.0, max=84.0, dynamic_range=4.0, mostly_dark=false, visible_content_candidate=false
default_mjpg_640x480: mean=1.0, min=1.0, max=1.0, dynamic_range=0.0, mostly_dark=true, visible_content_candidate=false
default_yuyv_640x480: mean=0.227723, min=0.0, max=1.125, dynamic_range=1.125, mostly_dark=true, visible_content_candidate=false
```

claim_boundary 已收紧为：采样链路成功；默认样本黑场，调亮/手动曝光样本均匀灰/白且动态范围不足，因此 `visible_content_proven=false`；不能证明可用环境视觉内容。

人工查看 `camera_visibility_contact_sheet.jpg`：联系图是两块灰/白面板和两块黑色面板，没有可复核环境纹理或结构。默认 MJPG/YUYV 为黑场；临时调亮和手动曝光样本虽然不是 `mostly_dark`，但 `dynamic_range_luma` 只有 0.0 或 4.0，仍缺少纹理证据。因此本轮证明了 `/dev/video1` 可以采样，证明了亮度/曝光控制会改变输出亮度，但没有证明摄像头已提供可用于路线、定位或视觉识别的环境内容。

## 失败定位

没有发生 SSH、V4L2 枚举或帧采集失败。诊断定位为：

- 默认相机输出仍是黑场，和上一轮关键帧几乎全黑一致。
- 临时提高 brightness/gain/backlight 或手动曝光后，图像变亮但几乎无动态范围，表现为均匀灰/白场，不是可复核环境内容。
- 可能根因包括：镜头盖/遮挡、摄像头朝向纯黑或纯白表面、现场暗环境、镜头未对准有效场景、驱动/设备输出被固定填充值、上层 ROS camera path 使用了错误节点或覆盖了 V4L2 控制项。
- `ros2` 在当前 SSH root shell 中显示缺失，因此本轮没有复用 ROS2 camera path；该点不影响 V4L2 设备级诊断，但需要后续进入实际 ROS2 运行环境复核 `/camera/image_raw` 是否绑定 `/dev/video1`。

## 剩余风险

- motion_commands_sent=false：本轮没有发底盘运动命令，也不证明运动安全。
- safe_to_control=false：本轮只是相机诊断，不构成自主运行准入。
- delivery_success=false：本轮没有验证垃圾投递、到站、返回或用户任务闭环。
- visible_content_proven=false：本轮没有证明摄像头画面包含可用环境内容，不能用来支撑视觉定位、关键帧路线、障碍检测或语义识别能力。
- 下一步应在现场确认镜头盖/遮挡和光照，摆放带纹理的高对比目标后重新采样；同时确认 ROS camera 节点实际使用 `/dev/video1`，并采集一段短视频或连续帧排除单帧启动瞬态。
