# Board Camera Visibility Probe Micro Sprint

- sprint_type: micro
- owner: robot-hardware-engineer
- time: 2026-06-10 03:50-03:52 Asia/Shanghai
- motion_commands_sent=false
- camera_device_opened=true
- ros_camera_topic_proven=true
- visible_content_proven=false
- probable_failure_class=physical_occlusion_or_dark_scene

## 设计决策

本轮目标是在真实上位机 `root@192.168.1.11:37878` 上把 `/dev/video1` 的可见性问题一次性拆成三层证据：

1. 设备事实：用 `v4l2-ctl`、`ls -l /dev/video*` 和占用检查确认 `/dev/video1` 仍是 UVC capture 节点，记录格式、控制项和当前曝光/亮度/增益。
2. OpenCV 直接采样：至少覆盖 `640x480` 与 `320x240`，并尽量分别测试 MJPG/YUYV；每组保存 frame 和 metrics JSON，指标包含 `width/height/read_ok/mean_luma/dynamic_range_luma/non_black_ratio/laplacian_var/edge_count`。
3. ROS topic smoke：启动 `ros2_trashbot_vision camera_publisher`，从 `/camera/image_raw` 采一帧并计算同样指标，确认默认 launch 相机入口仍能发布 topic。

可见内容判据采用保守阈值：需要采样成功、平均亮度不接近黑场、非黑像素比例足够、动态范围或纹理指标足够。均匀灰/白帧只能说明控制链路能改变亮度，不计为 `visible_content_proven=true`。

## 验收口径

- 必须记录 SSH 连通、主机名和时间。
- 必须记录 `/dev/video1` 的 V4L2 设备事实、格式列表、控制项和占用状态。
- 必须保存 OpenCV direct frames + per-sample metrics JSON。
- 必须保存 ROS `/camera/image_raw` sample + metrics JSON，并记录 publisher 清场结果。
- 必须输出布尔结论：`camera_device_opened`、`ros_camera_topic_proven`、`visible_content_proven`、`motion_commands_sent=false`。
- 必须给出 `probable_failure_class` 和理由。

## 风险边界

- 本轮不发送 `/cmd_vel`，不启动底盘控制，不停止或改写 WAVE ROVER/ESP32 固件。
- V4L2 control sweep 只做保守临时设置；执行前记录原值，结束后恢复并保存恢复检查。
- 如果画面仍不可见，不能美化为视觉可用，只记录下一步需要现场人工确认镜头盖、遮挡、朝向、补光、USB 口或相机本体。
- 如果画面可见，本轮只证明相机内容可见，不证明真实运动、导航、路线关键帧或送达闭环。

## 已读资料来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vision/board_camera_publisher.md`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py`

采用的硬件事实边界：

- `docs/vendor/VENDOR_INDEX.md` 指定项目主 SBC 为 Orange Pi Zero 3，Waveshare 上位机资料是 Raspberry Pi 参考，不能直接推断 Orange Pi CSI/Picamera2。
- `cv_ctrl.py` 的 USB 分支采用 `cv2.VideoCapture(0)`，本项目只采纳 USB/OpenCV 入口思路，不采纳 Raspberry Pi 专属相机路径。
- `config.yaml` 中 vendor 默认视频尺寸为 `640x480`，本轮把 `640x480` 作为主采样规格，同时补 `320x240` 降级规格。

## 执行记录

实际改动文件：

- `docs/vision/board_camera_publisher.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/tech-done.md`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/opencv_visibility_probe.py`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/ros_image_metrics_probe.py`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/ssh_connected.log`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/remote_device_facts.log`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/remote_opencv_probe.log`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/remote_ros_probe.log`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/remote_final_cleanup_check.log`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/remote_camera_visibility_probe.tgz`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/artifacts/rober_camera_visibility_probe_0400/**`

远端 artifacts：

- OpenCV summary：`artifacts/rober_camera_visibility_probe_0400/opencv/opencv_visibility_summary.json`
- OpenCV frames：`artifacts/rober_camera_visibility_probe_0400/opencv/*.jpg`
- per-sample metrics：`artifacts/rober_camera_visibility_probe_0400/opencv/*.metrics.json`
- controls：`artifacts/rober_camera_visibility_probe_0400/opencv/controls_before.json`、`controls_after_restore.json`
- ROS metrics：`artifacts/rober_camera_visibility_probe_0400/ros/ros_image_metrics.json`
- ROS sample：`artifacts/rober_camera_visibility_probe_0400/ros/ros_camera_image_raw_sample.jpg`
- ROS launch log：`artifacts/rober_camera_visibility_probe_0400/ros/bringup_camera.log`
- final cleanup：`artifacts/rober_camera_visibility_probe_0400/ros/final_cleanup_check.log`

SSH 连通：

```text
connected
op-z3-b6.home
Wed Jun 10 03:50:47 AM CST 2026
```

设备事实命令已执行并保存到 `artifacts/remote_device_facts.log`：

```text
USB Composite Device: DV20 USB  (usb-5310000.usb-1):
        /dev/video1
        /dev/video2

/dev/video1 Driver name: uvcvideo
/dev/video1 Card type: USB Composite Device: DV20 USB
/dev/video1 Device Caps: Video Capture, Streaming, Extended Pix Format
/dev/video1 formats:
  MJPG: 1280x720, 640x480, 480x320, 1920x1080 @30fps
  YUYV: 640x480 @22fps, 320x240 @25/20fps
lsof /dev/video1: no output
fuser -v /dev/video1: no output
```

控制项原值：

```text
brightness=0
contrast=0
saturation=0
gamma=10
gain=4
backlight_compensation=0
auto_exposure=3
exposure_time_absolute=80
```

ROS smoke 第一次执行失败：

```text
/opt/ros/humble/setup.bash:.:11: no such file or directory: /root/rober/onboard/setup.sh
```

定位：远端默认 shell 不是 bash，直接 `source /opt/ros/humble/setup.bash` 被错误解释。改用 `bash -lc` 后重跑通过，不属于 ROS 包或 camera 失败。

## 验证结果

OpenCV 直接采样矩阵：

| sample | read_ok | actual | mean_luma | dynamic_range_luma | non_black_ratio | laplacian_var | edge_count | visible |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `default_mjpg_640x480` | true | 640x480 MJPG | 1.0 | 0.0 | 0.0 | 0.0 | 0 | false |
| `default_yuyv_640x480` | true | 640x480 YUYV | 0.001237 | 1.0 | 0.0 | 0.010768 | 0 | false |
| `default_mjpg_320x240` | true | 480x320 MJPG | 1.0 | 0.0 | 0.0 | 0.0 | 0 | false |
| `default_yuyv_320x240` | true | 320x240 YUYV | 0.000755 | 1.0 | 0.0 | 0.006693 | 0 | false |
| `boosted_mjpg_640x480` | true | 640x480 MJPG | 1.0 | 0.0 | 0.0 | 0.0 | 0 | false |

保守 sweep：

```text
brightness target=63 ok=true
gain target=5 ok=true
backlight_compensation target=255 ok=true
```

sweep 后仍没有可见内容，随后控制项恢复。`exposure_time_absolute` 恢复写入返回 false，因为当前 `auto_exposure=3` 时该控制项为 inactive；最终读数仍为原值 `80`。

ROS camera topic smoke：

```text
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

本轮故意不传 `camera_device`，用于验证默认 launch 路径。`bringup_camera.log` 关键输出：

```text
[camera_publisher-3] [INFO] ... camera_publisher streaming /dev/video1 to /camera/image_raw with frame_id=camera, requested 640x480@2.00fps
```

Topic 输出：

```text
/camera/image_raw
Type: sensor_msgs/msg/Image
Publisher count: 1
```

`ros2 topic hz` 在 8 秒窗口内输出：

```text
WARNING: topic [/camera/image_raw] does not appear to be published yet
```

但同一轮 Python subscriber 成功收到一帧，因此 topic 主链路以 subscriber 证据为准：

```text
image_message_observed=true
height=480
width=640
encoding=bgr8
step=1920
data_len=921600
mean_luma=0.001243
dynamic_range_luma=1.0
non_black_ratio=0.0
laplacian_var=0.009538
edge_count=0
visible_content_candidate=false
```

清场检查：

```text
matching processes: no output
lsof /dev/video1: no output
fuser -v /dev/video1: no output
brightness=0
gain=4
backlight_compensation=0
auto_exposure=3
exposure_time_absolute=80 flags=inactive
```

## 结论

- `camera_device_opened=true`：`/dev/video1` 是 DV20 USB UVC capture，OpenCV 每组均能打开并读取 frame。
- `ros_camera_topic_proven=true`：`bringup.launch.py` 默认 camera path 已使用 `/dev/video1`，`/camera/image_raw` 有 publisher，subscriber 收到完整 `640x480 bgr8` 图像。
- `visible_content_proven=false`：OpenCV direct 与 ROS topic 样本均为黑/近黑，`non_black_ratio=0.0`、`edge_count=0`，没有环境纹理或可用视觉内容。
- `motion_commands_sent=false`：本轮没有发布 `/cmd_vel`，没有启动底盘控制，没有写底盘串口。
- `probable_failure_class=physical_occlusion_or_dark_scene`。

分类理由：设备路径、驱动格式、OpenCV read、ROS publish/subscribe 均已成立；MJPG/YUYV 与两档分辨率均可读；临时 brightness/gain/backlight sweep 能写入并恢复，但输出仍没有非黑像素和边缘。因此更可能是镜头盖/保护膜/遮挡、朝向纯暗面、现场光照不足、USB 摄像头光学路径或相机本体输出黑场。`device_path_wrong` 和 `driver_format_issue` 不是当前首要分类。

## 剩余风险与下一步

- 需要现场人工确认镜头盖、保护膜、遮挡、朝向和补光；建议对准高对比纹理目标后复跑本轮 OpenCV + ROS 双路径采样。
- 如果现场确认无遮挡且补光后仍全黑，下一步更换 USB 口或 USB 摄像头本体，再复核 `/dev/video*` 枚举和 `/camera/image_raw`。
- 在 `visible_content_proven=true` 前，不应把 `/camera/image_raw` 用于路线关键帧、视觉定位、障碍检测、远程可视验收或外部运动证据。
- 本轮验证范围只覆盖 camera 可见性；不构成真实运动、Nav2、里程计、LiDAR motion delta、送达闭环或 HIL 安全准入。
