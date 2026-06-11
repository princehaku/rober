# Board Camera Publisher

`ros2_trashbot_vision/camera_publisher` 提供一个最小真实相机 ROS2 publisher，
用于把板上的 `cv2.VideoCapture` 设备发布到 `/camera/image_raw`，服务真实路线采样、
keyframe 证据和 bringup smoke。

## 设计边界

- 默认 **不启动**。只有 `bringup.launch.py` 显式传 `camera_enabled:=true` 时才拉起。
- 设备打不开时 **fail closed**：节点启动直接失败，不伪造帧，不回退到 mock 图像。
- 读帧失败时 **fail closed**：记录可读错误并跳过该帧，不补空白图。
- 不修改串口、底盘、速度、LiDAR 或 vendor firmware 默认值。

## 参数

- `device`：相机设备路径或数字索引；`bringup.launch.py` 与 `learn.launch.py` 现场默认 `/dev/video1`
- `topic`：发布 topic；默认 `/camera/image_raw`
- `frame_id`：图像 header frame；默认 `camera`
- `width`：请求宽度；默认 `640`
- `height`：请求高度；默认 `480`
- `fps`：请求帧率；默认 `15.0`

如果 `device` 是纯数字字符串（例如 `0`），节点会把它当作 OpenCV index；
否则按路径处理并展开 `~`。

## Launch 用法

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_topic:=/camera/image_raw \
  camera_frame_id:=camera \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=15.0
```

本轮 bringup smoke 只允许采样 topic，例如：

```bash
ros2 topic hz /camera/image_raw --window 2
ros2 topic echo --once /camera/image_raw
```

不允许因为验证相机而发布 `/cmd_vel`。

## 2026-06-09 sensor-only smoke 组合

从 `sprints/2026.06.09_23-20_board-bringup-blocker-fix` 开始，`bringup.launch.py`
新增 `base_enabled`，用于现场只验证传感器 topic 时跳过 `esp32_bridge`，避免
`upper_robot_api.py` 常驻占用 `/dev/ttyS5` 影响 smoke。推荐命令：

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

这个命令的目标仅是证明 `/camera/image_raw`、`/scan`、`/tf_static` 和 `/map`
能够共同进入 ROS graph，不代表：

- WAVE ROVER 底盘 UART 已通过 HIL；
- `base_link -> laser_frame` 已完成机械标定；
- 建图、导航或运动链路已经完成。

## 2026-06-09 实板设备结论

在 `root@192.168.1.11:37878` 实板上执行 `v4l2-ctl --list-devices` 和 OpenCV probe 后，确认：

- `/dev/video0` 是 `cedrus (platform:cedrus)`，属于 Orange Pi H618 的 V4L2 编解码设备，不是 USB 摄像头采集节点。
- `USB Composite Device: DV20 USB` 提供 `/dev/video1` 与 `/dev/video2`。
- 其中 `/dev/video1` 具备 `Video Capture` 能力，OpenCV 实测 `opened=True read=True`。
- `/dev/video2` 是 metadata 节点，OpenCV 不能作为图像输入打开。

因此当前实板的默认相机参数已经固化为：

```bash
camera_enabled:=true
```

`bringup.launch.py` 与 `learn.launch.py` 在 `camera_enabled:=true` 且未显式传
`camera_device` 时会使用 `/dev/video1`。`/dev/video0` 只适合作为失败样例保留在排查记录里，
不应继续作为这块板的现场采样设备假设。不同设备批次如枚举变化，仍可显式传
`camera_device:=...` 覆盖默认值。

## 2026-06-10 ROS2 topic path 结论

在 `root@192.168.1.11:37878` 实板上，root shell 直接执行 `ros2` 仍不在 `PATH`。
本轮确认可用的 ROS2 source 链是：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
```

source 后 `ros2 pkg prefix ros2_trashbot_vision` 和 `ros2 pkg prefix ros2_trashbot_bringup`
均能解析到 `/root/rober/onboard/install/...`。现场最小 camera publisher smoke 使用：

```bash
ros2 run ros2_trashbot_vision camera_publisher --ros-args \
  -p device:=/dev/video1 \
  -p topic:=/camera/image_raw \
  -p width:=640 \
  -p height:=480 \
  -p fps:=2.0
```

实测结果：

- `/camera/image_raw` 出现在 ROS graph，`ros2 topic info` 显示 `sensor_msgs/msg/Image`、`Publisher count: 1`。
- subscriber 收到 `640x480 bgr8` 图像，`step=1920`、`data_len=921600`。
- `ros_camera_topic_proven=true`：已证明 `/dev/video1` 可以经 `camera_publisher` 发布到 `/camera/image_raw`。
- `visible_content_proven=false`：图像仍近黑，`mean_luma=0.21674`、`dynamic_range_luma=0.9266`、`non_black_ratio=0.0`。

因此当前只能宣称 ROS2 camera topic 主链路可发布消息，不能宣称已经有可用视觉路线内容。
下一步必须在现场确认镜头盖、遮挡、朝向、光照和 USB 摄像头本体；在 `visible_content_proven=true`
之前，不应把该画面用于路线关键帧、视觉定位、障碍识别或远程可视验收。

当前实板仍以 `/dev/video1` 作为真实相机。`/dev/video0` 是 Cedrus decoder；
launch 默认值已从 `/dev/video0` 固化为 `/dev/video1`，因此现场运行可省略 `camera_device`：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

本轮只修正默认设备选择，`visible_content_proven=false` 仍成立：在可见内容被证明前，
不能把这路画面用于路线关键帧、视觉定位、障碍识别或远程可视验收。

## 2026-06-11 17:00 current camera visible content probe

`sprints/2026.06.11_17-00_current_camera_visible_content_probe/` 只做 camera-only
当前状态再判定，没有触碰底盘、Nav2、雷达或手动运动。真实上位机
`http://192.168.1.11:8787` 读回仍显示 `active_peer_count=0`。

远端 `/dev/video1` 的 default OpenCV probe 结果是：

- `open_ok=true`
- `read_ok=false`
- `attempts=12`
- `first_frame_timeout=true`

后续只启动到 `mjpg_640x480_set_fmt.txt`，没有形成可用 sample JPG 或有效 frame metrics JSON，
也没有把相机状态升级为 `visible_content_proven=true`。因此当前更像
`first-frame timeout`，不是已恢复可见内容，也还没有进入可稳定判定的 near-black frame
采样阶段。

## 2026-06-11 18:20 live evidence sweep camera readback

`sprints/2026.06.11_18-20_board_live_evidence_sweep/` 重新读取真实上位机 camera
health/devices，只做 camera-only 状态和设备复查，没有打开点动、Nav2 执行或底盘运动。

`GET /api/camera/health` 返回 HTTP 200，核心字段：

- `status=ready`
- `host=op-z3-b6.home`
- `video_source=auto`
- `active_peer_count=0`
- `active_frames_read=0`
- `active_camera_read_failures=0`
- `safe_to_control=false`
- `robot_control_executed=false`

`GET /api/camera/devices` 返回 HTTP 200，`v4l2-ctl --list-devices` 仍显示：

```text
cedrus (platform:cedrus):
        /dev/video0
        /dev/media0

USB Composite Device: DV20 USB  (usb-5310000.usb-1):
        /dev/video1
        /dev/video2
        /dev/media1
```

因此 `/dev/video1` 仍是当前实板 DV20 USB UVC capture 节点，`/dev/video0` 仍是
Cedrus decoder。由于本轮没有成功采集可见 frame，且 `/api/operator/report` 仍为
`visible_content_proven=false`、`camera_artifacts_ref=not_attached_no_motion_smoke`，
当前只能证明 camera service/device readback 可用，不能把视觉内容用于路线关键帧、
视觉定位、障碍识别或远程可视验收。

## 2026-06-11 20:05 camera visible content gate refresh

`sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/` 继续只做
camera-only 复核，没有调用 `/api/base/manual`，没有发布 `/cmd_vel`，没有执行
Nav2/NavigateToPose，也没有打开底盘 `/dev/ttyS5`。

本轮采用的本地 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/12/flask_camera.py`

真实上位机 `root@192.168.1.11:37878` 与 Robot API `http://192.168.1.11:8787`
读回显示 camera service 仍为 `status=ready`，`active_peer_count=0`。V4L2 事实保持：
`/dev/video1` 是 `uvcvideo` 的 `USB Composite Device: DV20 USB`，具备
`Video Capture`，支持 `MJPG 640x480 @ 30fps` 和 `YUYV 640x480 @ 22fps`。

短超时 OpenCV direct probe 结果：

| 样本 | open_ok | read_ok | first_frame_timeout | 实际格式 | visible_content_proven |
| --- | --- | --- | --- | --- | --- |
| `default` | true | false | true | `YUYV 640x480 @ 22fps` | false |
| `mjpg_640x480` | true | false | true | `MJPG 640x480 @ 30fps` | false |
| `yuyv_640x480` | true | false | true | `YUYV 640x480 @ 22fps` | false |

由于底层 direct frame 没有任何 `read_ok=true` 样本，本轮没有 sample JPG/PNG，也没有
可见 frame luma/edge metrics；`visible_content_proven=false` 保持成立。未执行
PC/WebRTC offer self-test，原因是 direct frame 尚不可用，继续验证上层信令不能证明
“实时图传能看到可见内容”。

本轮已把 `/api/operator/report` 更新为
`site_state=camera_direct_first_frame_timeout`，且 `visible_content_proven=false`、
`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`
全部保持。下一步应转现场硬件动作：检查 DV20 输入源/镜头盖/保护膜/遮挡/朝向/补光，
并用 known-good UVC USB 摄像头替换验证。

## 2026-06-11 19:14 local WebRTC camera service 入仓

本轮把真实板端正在运行的 8088 camera WebRTC 服务正规化为仓库脚本
`onboard/scripts/local_webrtc_camera_smoke.py`。服务提供：

- `GET /health`：返回 `schema=trashbot.local_webrtc_camera_smoke.v1`、`app`、
  `status`、`video_source`、`video_source_mode`、active peer/frame/failure 计数、
  `system_diagnostics`、`media_diagnostics`、`source_candidates_summary` 和
  `current_selection`；安全字段固定 `safe_to_control=false`、
  `robot_control_executed=false`、`delivery_success=false`、
  `primary_actions_enabled=false`。
- `GET /devices`：成功 schema 保持历史兼容
  `trashbot.local_webrtc_camera_devices.v1`；只读枚举 `/dev/video*`、
  `v4l2-ctl --list-devices`、`--all` 和 `--list-formats-ext`，不写 V4L2
  controls，不打开底盘串口。
- `POST /offer`：成功 schema 保持历史兼容
  `trashbot.local_webrtc_camera_offer.v1`；校验 `type=offer` 和非空 SDP 后，只有在 `aiortc/cv2/av`
  存在且 OpenCV 从真实源读到首帧时才创建 WebRTC answer；依赖缺失、
  invalid offer 或首帧不可读均结构化 fail-closed，不生成黑帧或 placeholder。
- `POST /peers/{peer_id}/close`：成功 schema 保持历史兼容
  `trashbot.local_webrtc_camera_close.v1`；释放 `RTCPeerConnection`、track 和
  `VideoCapture`，并在 `/health.media_diagnostics.last_closed_peer` 回读 close
  摘要。

`--video-source auto` 只用只读设备能力做选择：跳过 Cedrus decoder、metadata
节点和非 `Video Capture` 候选，优先 UVC/USB capture。按当前实板事实，auto 应选择
`/dev/video1`；如果现场显式传 `--video-source /dev/videoX`，服务会尊重显式源，
不再自动切换。该入仓动作只让服务可复现、可测试、可诊断；它没有解决
`/dev/video1` 当前 direct `first-frame timeout`，也不证明 PC 可见内容已恢复。

## 2026-06-11 20:55 local WebRTC camera service 上板部署

`sprints/2026.06.11_20-55_camera_service_board_deploy/` 已把仓库内
`onboard/scripts/local_webrtc_camera_smoke.py` 部署到真实上位机
`root@192.168.1.11:37878`，并重启 `trashbot-local-webrtc-camera.service`。

部署过程中真实板端暴露了一个 auto 选源兼容问题：DV20 `/dev/video1` 的全局
Capabilities 同时包含 `Video Capture` 与 `Metadata Capture`，但它的 `Device Caps`
与格式表实际是图像采集。代码已改为以 `Format Video Capture`、`MJPG`、`YUYV`
等真实图像帧格式作为图像节点判据，避免把 `/dev/video1` 误判为 metadata。

修复后，直接 8088 与经 8787 Robot API 代理读回一致：

- `/health`：`schema=trashbot.local_webrtc_camera_smoke.v1`，
  `status=ready`，`video_source=/dev/video1`，`video_source_mode=auto`，
  `active_peer_count=0`，`safe_to_control=false`，`robot_control_executed=false`。
- `/devices`：`schema=trashbot.local_webrtc_camera_devices.v1`，
  `status=loaded`，`paths=["/dev/video0","/dev/video1","/dev/video2"]`。
- auto 选择分数：`/dev/video0=-895` 且 `is_decoder=true`，
  `/dev/video1=148` 且 `is_video_capture=true`，
  `/dev/video2=-1055` 且 `is_metadata=true`。

真实 `aiortc` recvonly offer smoke 仍返回 fail-closed：

- `offer_http_status=503`
- `offer_error=first_frame_unreadable`
- `offer_failure_reason=first_frame_timeout`
- `offer_video_source=/dev/video1`
- `peer_id=None`
- offer 后 `/health.active_peer_count=0`

因此当前结论更新为：camera service 已由仓库版本在真实上位机复现，并能稳定识别
`/dev/video1`；但 `/dev/video1` 首帧仍不可读。PC 实时图传可见内容仍未恢复，
下一步必须做 DV20 输入源/线缆/供电/采集卡状态检查或 known-good USB UVC 替换验证。

## 本地资料来源

- `docs/vendor/VENDOR_INDEX.md`
  - 明确 Orange Pi Zero 3 是项目主 SBC，不能把 Raspberry Pi 假设直接当项目结论。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor `base_config.use_lidar: false` 说明 LiDAR 在参考 app 中是可选能力，因此本项目也保持 launch 默认关闭。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - vendor Raspberry Pi 参考 app 的 USB camera 分支使用 `cv2.VideoCapture(0)`。
- `root@192.168.1.11` 实板命令证据
  - `v4l2-ctl --list-devices`
  - `v4l2-ctl --all -d /dev/video1`
  - OpenCV `VideoCapture('/dev/video1')`
- `docs/interfaces/o7_realtime_hardware_sources.md`
  - 明确 vendor app 只证明 Raspberry Pi 参考能力，不证明 Orange Pi CSI、Picamera2、
    ALSA 编号或 RTC/云端链路已在 rober 项目中打通。

因此当前实现只采纳 vendor 的最小 USB/OpenCV 入口思路，不引入 Raspberry Pi
`Picamera2`、boot overlay 或音视频栈假设。

## 2026-06-10 04:00 camera visibility probe

`sprints/2026.06.10_04-00_board_camera_visibility_probe/` 在真实上位机
`root@192.168.1.11:37878` 上把设备层、OpenCV 直采和 ROS topic 三段证据放在同一轮复核。
本轮未发送 `/cmd_vel`，未启动底盘控制。

设备事实保持不变：

- `/dev/video1` 是 `uvcvideo` 驱动的 `USB Composite Device: DV20 USB`，具备 `Video Capture`。
- `/dev/video0` 仍是 `cedrus (platform:cedrus)`，不是相机采集节点。
- `/dev/video2` 仍是同一个 UVC 设备的 metadata 节点。
- `/dev/video1` 支持 `MJPG`：1280x720、640x480、480x320、1920x1080；支持 `YUYV`：640x480、320x240。

OpenCV 直采矩阵结论：

| 样本 | read_ok | mean_luma | dynamic_range_luma | non_black_ratio | edge_count | 结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `default_mjpg_640x480` | true | 1.0 | 0.0 | 0.0 | 0 | 不可见 |
| `default_yuyv_640x480` | true | 0.001237 | 1.0 | 0.0 | 0 | 不可见 |
| `default_mjpg_320x240` | true | 1.0 | 0.0 | 0.0 | 0 | 不可见；设备实际输出 480x320 |
| `default_yuyv_320x240` | true | 0.000755 | 1.0 | 0.0 | 0 | 不可见 |
| `boosted_mjpg_640x480` | true | 1.0 | 0.0 | 0.0 | 0 | 保守 brightness/gain/backlight sweep 后仍不可见 |

ROS topic smoke 结论：

- `bringup.launch.py base_enabled:=false camera_enabled:=true camera_width:=640 camera_height:=480 camera_fps:=2.0`
  未显式传 `camera_device` 时，`camera_publisher` 日志显示使用 `/dev/video1`。
- `/camera/image_raw` 出现在 ROS graph，`ros2 topic info` 显示 `sensor_msgs/msg/Image`、`Publisher count: 1`。
- subscriber 收到 `640x480 bgr8` 图像，`data_len=921600`。
- ROS topic 样本指标：`mean_luma=0.001243`、`dynamic_range_luma=1.0`、
  `non_black_ratio=0.0`、`edge_count=0`。

布尔结论：

- `camera_device_opened=true`
- `ros_camera_topic_proven=true`
- `visible_content_proven=false`
- `probable_failure_class=physical_occlusion_or_dark_scene`

失败分类理由：设备枚举、OpenCV read、ROS publish/subscribe 都成立，MJPG/YUYV 和两档分辨率均能读到帧，
保守 brightness/gain/backlight sweep 后控制项恢复正常，但所有样本仍没有非黑像素和边缘纹理。
因此当前更像镜头盖/遮挡、朝向纯暗面、现场光照不足、相机本体输出黑场，或 USB 摄像头光学路径问题；
驱动格式错误和设备路径错误的概率低于物理遮挡/暗场。

后续路线关键帧、视觉定位、障碍识别或远程可视验收前，必须先由现场人工完成：

1. 确认镜头盖、保护膜、遮挡和摄像头朝向。
2. 对准有纹理的高对比目标，并打开补光。
3. 必要时更换 USB 口或 USB 摄像头本体后重跑本 sprint 的 OpenCV/ROS 双路径采样。

## 2026-06-11 13:25 camera visible gate live probe

`sprints/2026.06.11_13-25_camera_visible_gate_live_probe/` 在真实上位机
`root@192.168.1.11:37878` 上做了非运动 live recovery/probe。本轮只读或临时
设置 V4L2 camera controls，并在结束时恢复；未调用 `/api/base/manual`，未发布
`/cmd_vel`，未触碰 WAVE ROVER 底盘串口或运动配置。

资料来源仍以 `docs/vendor/VENDOR_INDEX.md` 为入口，并只引用 camera 相关本地资料：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`：vendor 视频默认
  `640x480`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`：vendor Raspberry Pi 参考
  app 优先 USB camera，使用 OpenCV `VideoCapture`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_en/12/flask_camera.py` 与
  `tutorial_cn/12/flask_camera.py`：Picamera2/JPEG streaming 只是 Raspberry Pi/CSI
  参考，本项目 Orange Pi + DV20 不能直接照搬。

设备事实保持不变：

- `/dev/video0` 是 `cedrus (platform:cedrus)` 编解码设备，不是相机采集节点。
- `/dev/video1` 是 `uvcvideo` 的 `USB Composite Device: DV20 USB`，具备
  `Video Capture`。
- `/dev/video2` 是同一 DV20 的 metadata 节点，不是可用图像采集节点。
- camera service 当前 `video_source=auto`，`/api/camera/health` 显示 active peers 为
  `0`，last closed peer 曾自动选择 `/dev/video1` 并读到 `108` 帧。

OpenCV 采样覆盖 `/dev/video1` 默认、`MJPG`/`YUYV`、`640x480`、`1280x720`、
`1920x1080`、`320x240`，并试过一次可恢复的 controls boost 与 manual exposure。
所有默认/格式样本仍接近黑场：

| 样本 | read_ok | mean_luma | max_luma | nonblack_ratio_gt10 | 结论 |
| --- | --- | ---: | ---: | ---: | --- |
| `video1_default` | true | 0.0011458333 | 1 | 0.0 | 不可见 |
| `video1_mjpg_640x480` | true | 1.0 | 1 | 0.0 | 不可见 |
| `video1_yuyv_640x480` | true | 0.0008658854 | 1 | 0.0 | 不可见 |
| `video1_mjpg_1280x720` | true | 1.0 | 1 | 0.0 | 不可见 |
| `video1_mjpg_1920x1080` | true | 1.0 | 1 | 0.0 | 不可见 |
| `video1_yuyv_320x240` | true | 0.0013802083 | 1 | 0.0 | 不可见 |
| `video1_boosted_controls_mjpg_640x480` | true | 1.0 | 1 | 0.0 | 不可见 |
| `video1_manual_exposure_mjpg_640x480` | true | 7.29296875 | 59 | 0.172783203125 | 极暗轮廓，不足以通过 gate |

manual exposure 样例能看到很弱的暗场轮廓，但仍不足以声明稳定可见内容。最终 controls 已恢复：

```text
brightness: 0
contrast: 256
saturation: 250
gamma: 20
gain: 4
power_line_frequency: 0
white_balance_temperature: 4500
sharpness: 100
backlight_compensation: 0
auto_exposure: 3 (Aperture Priority Mode)
exposure_time_absolute: 80
```

布尔结论：

- `camera_device_opened=true`
- `camera_service_active=true`
- `active_peers=0`
- `visible_content_proven=false`

因此手动运动/HIL gate 仍不得放行。下一步现场动作必须先处理镜头盖/保护膜/遮挡/朝向/光照；
如果 DV20 是采集卡，还要确认 HDMI/AV视频源是否已接入且不是黑屏；必要时插入 known-good
USB UVC camera 后重跑 `/api/camera/devices` 与 OpenCV stats。

## 2026-06-11 14:45 camera visible recovery matrix

`sprints/2026.06.11_14-45_camera_visible_recovery_matrix/` 在真实上位机
`root@192.168.1.11:37878` 上继续做 camera-only V4L2/OpenCV 恢复矩阵。本轮不改
`camera_publisher`、bringup、launch 或任何产品代码；未写 WAVE ROVER UART，未调用
`/api/base/manual` 非 stop，未发布 `/cmd_vel`，未执行 Nav2。

资料来源边界：

- WAVE ROVER 底盘安全边界来自 `docs/vendor/VENDOR_INDEX.md`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 和
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`。
- 底盘 UART 是 newline-delimited UTF-8 JSON；vendor Raspberry Pi 串口路径不能外推到
  Orange Pi；`T=1/T=13/T=130/T=131` 均未在本轮执行。

格式/分辨率覆盖：

| 样本 | 请求 | 实际 | gray_mean | gray_max | non_black_ratio_ge16 | 结论 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `orig_mjpg_640x480` | MJPG 640x480 | MJPG 640x480 | 1.0 | 1 | 0.0 | 不可见 |
| `orig_mjpg_1280x720` | MJPG 1280x720 | MJPG 1280x720 | 1.0 | 1 | 0.0 | 不可见 |
| `orig_mjpg_320x240_request` | MJPG 320x240 | MJPG 480x320 | 1.0 | 1 | 0.0 | 不可见 |
| `orig_yuyv_640x480` | YUYV 640x480 | YUYV 640x480 | 0.000820 | 2 | 0.0 | 不可见 |
| `orig_yuyv_320x240` | YUYV 320x240 | YUYV 320x240 | 0.000964 | 1 | 0.0 | 不可见 |

控制矩阵覆盖原始控制、auto exposure boost、manual exposure 80/1000/10000/50000。
其中最高曝光档：

- `ctrl_manual_exp_50000_gain7_boost_mjpg_640x480`
- `gray_mean=5.280280`
- `gray_max=40`
- `non_black_ratio_ge16=0.004417`
- `edge_count=391`
- 可见极暗轮廓，但不足以作为路线关键帧、视觉定位、障碍识别或远程可视验收。

最终结论：

- `camera_device_opened=true`
- `visible_content_proven=false`
- `probable_failure_class=physical_occlusion_dark_scene_or_input_source_black_frame`
- 更具体地看，最高曝光档出现暗轮廓，说明格式/路径错误概率较低；现场最应先排查
  镜头盖/保护膜/遮挡、朝向纯暗面、环境光不足和 DV20 输入源黑屏。

控制恢复状态：

- 初次脚本恢复后发现 inactive 的 `exposure_time_absolute` 仍为 `50000`。
- 已补恢复为 `auto_exposure=3`、`exposure_time_absolute=80 flags=inactive`。
- 最终 readback 与 `lsof/fuser` 清场证据见
  `sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/final_remote_readback_after_restore_rerun.log`。

在 `visible_content_proven=true` 前，`/dev/video1` 仍只能用于链路存在性证明，
不能用于 motion gate 放行。

## 2026-06-11 16:05 camera first-frame recovery probe

`sprints/2026.06.11_16-05_camera_first_frame_recovery_probe/` 在真实上位机
`root@192.168.1.11:37878` 上做了一次更窄的 first-frame recovery probe，
目标不是证明画面是否可见，而是判断当前 `preview_open_result=start_failed` /
`failure_reason=The operation was aborted due to timeout` 是否来自前端、camera service，
还是 `/dev/video1` 自身首帧 readback 卡死。

本轮资料边界继续以 `docs/vendor/VENDOR_INDEX.md` 为入口，并采用：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - vendor 底盘控制走 `/dev/ttyAMA0 @ 115200` UART JSON，这一事实只用于界定
    WAVE ROVER 底盘链路边界，不外推到 Orange Pi 当前设备名。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - vendor 参考上位机把 USB camera 作为 `cv2.VideoCapture(...)` 输入源；
    相机路径与底盘 UART 是两条独立链路。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor 视频默认分辨率 `640x480`。

因此本轮明确结论是：DV20 `/dev/video1` 的 UVC/V4L2 首帧读取问题，不属于
WAVE ROVER `T=1/T=13/T=130/T=131`、`/cmd_vel`、`/dev/ttyS5` 或底盘 UART 范畴。
本轮实际未调用 `/api/base/manual`、未发布 `/cmd_vel`、未占用 `/dev/ttyS5`。

重启前 readback：

- `/api/camera/health` 显示上一次失败 peer 的 `source_selection` 为：
  - `/dev/video0 opened=false`
  - `/dev/video1 opened=true read_ok=false`
  - `/dev/video2 opened=false`
  - `failure_reason=no_candidate_opened_and_read_first_frame`
- `journalctl -u trashbot-local-webrtc-camera.service` 记录：
  - 14:25 的旧 peer 曾在 `/dev/video1` 上稳定编码 `5653` 帧。
  - 15:57 的失败 peer 对 `/dev/video1` 触发
    `VIDEOIO(V4L2:/dev/video1): select() timeout`，随后 `offer_failed`。
- probe 前 `lsof/fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 均无残留占用。

最小 OpenCV first-frame probe（重启前）：

- `MJPG 640x480`：`opened=true`，`read_ok=false`，约 `40.7s` 内四次读帧全部超时。
- `YUYV 640x480`：`opened=true`，`read_ok=false`，约 `40.7s` 内四次读帧全部超时。
- `MJPG 1280x720`：`opened=true`，`read_ok=false`，约 `40.7s` 内四次读帧全部超时。
- 因为一帧都没有读到，所以本轮没有 `frame_shape/gray_mean/gray_max/non_black_ratio`，
  也没有 sample JPG artifact。

安全重启 `trashbot-local-webrtc-camera.service` 后：

- service 恢复 `active`，`/api/camera/health` 返回 `status=ready`、`active_peer_count=0`。
- 直接访问板端 `http://127.0.0.1:8088/health` 也返回 `200 OK`。
- 但同一组 OpenCV probe 结果不变：三种模式全部 `opened=true read_ok=false`，并继续出现
  `VIDEOIO(V4L2:/dev/video1): select() timeout`。

因此当前更接近以下结论，而不是“前端 preview 状态脏了”：

1. `trashbot-local-webrtc-camera.service` 本身可以被安全重启并恢复到 `active/ready`。
2. 当前失败点停留在更底层的 `/dev/video1` 首帧 readback；仅重启 camera service
   不能恢复。
3. 由于 probe 前后都没有 `/dev/video1` 占用者，当前不像普通的 device busy，更像
   DV20/UVC 流在设备或物理输入侧进入了“可 open、不可 first-frame read”状态。
4. 结合 14:25 曾稳定出帧、16:05 后稳定 read timeout，本轮更偏向“DV20/物理输入源/
   设备临时卡死或黑场上游异常”，而不是单纯的上位机 HTTP/WebRTC service 状态问题。

cleanup 结果：

- `trashbot-local-webrtc-camera.service` 结束时保持 `active`。
- `/api/camera/health` 最终 `active_peer_count=0`。
- `/dev/video0`、`/dev/video1`、`/dev/video2`、`/dev/ttyS5` 的 `lsof/fuser`
  结束时均无本轮残留占用。
