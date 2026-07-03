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

## 2026-06-26 18:55 当前 DV20 首帧 fail-fast 状态

本节覆盖下面历史 smoke 中“MJPEG fallback 可见”的旧现场状态。当前真实上位机
`root@192.168.1.11:37878` 上，`/dev/video1` 仍是 DV20 UVC capture，8088 camera
service 已部署仓库版 `onboard/scripts/local_webrtc_camera_smoke.py` 并以
`--fps 30` 运行，但 DV20 设备当前不出首帧：

- 直连 `GET http://192.168.1.11:8787/api/camera/mjpeg` 在约 4 秒内返回 HTTP 502，
  上游 8088 返回 HTTP 503，body 为 `error=first_frame_unreadable`、
  `failure_reason=capture_read_returned_false`。
- 8088 `/health` 顶层状态已从泛化 `ready` 回写为
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=capture_read_returned_false`。
- PC `GET /api/robot-control/summary` 读回同一状态：
  `camera.status=source_first_frame_failed`、`selected_path=/dev/video1`、
  `last_offer_failure_reason=capture_read_returned_false`。
- `camera/first-frame/probe` 仍返回 `probe_failed/open_failed`，没有
  `visible_content_proven`，不能把摄像头用于建图可见内容证明。

代码侧修正是：`SharedCameraCapture.read_frame_with_timeout()` 会在 V4L2
`capture.read()` 卡住或返回 false 时快速 fail-closed，并释放共享 capture；MJPEG
在写 HTTP 200 前必须先拿到真实首帧。这样 PC 画面卡片会看到明确失败态，而不是
“相机 ready 但一直等待画面”。该修正不发布 `/cmd_vel`，不调用底盘串口，不改变
`safe_to_control=false`、`robot_control_executed=false`。

下一步仍是硬件/驱动层排查：复位或更换 DV20、检查 USB 供电和视频输入源，或接入
known-good UVC 摄像头验证 `/dev/video1` 出帧链路。

## 2026-07-03 21:55 DV20 高速 USB 仍无帧与探针修正

本轮按 `docs/vendor/VENDOR_INDEX.md` 的硬件资料入口复核 Orange Pi Zero 3 USB/UVC
排查边界，只触碰相机诊断脚本，不修改底盘、UART、雷达或运动控制。真实上位机
`root@192.168.1.11 -p 7878` 当前事实：

- `/dev/video1` 仍是 `USB Composite Device: DV20 USB` 的 `Video Capture` 节点，`/dev/video2` 是 metadata。
- `trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service` active，`/dev/video1` 无其它 owner。
- `v4l2-ctl` 直接抓 `MJPG@640x480` 输出 0 字节；`ffmpeg` 能看到 MJPEG 流声明但等不到可解码帧。
- `/api/camera/usb-recovery` 停服务、关闭 autosuspend、reauthorize USB 后，USB video speed 为 `480M`，但 `YUYV@320x240@20` 和 `MJPG@480x320@30` 仍 0 字节超时。

因此当前图传缺口继续归因为 DV20/UVC 源头无视频 buffer，不是 PC 页面、多人共享预览或浏览器独占。
软件侧修正为：上位机 `camera_probe_fallback_requests()` 先覆盖 320x240/160x120 低负载模式，
再回到常规 640/720p；PC 代理会顶层暴露 `fallback_attempts`、`low_bandwidth_fallback_attempted`
和压缩后的 `probe_payload`。这只增强诊断可见性，不能替代检查摄像头线缆、供电、输入源或
换 known-good UVC 复测。

## 2026-06-26 20:00 首帧证明门禁

本轮按 `docs/vendor/VENDOR_INDEX.md` 入口复核 vendor 资料边界：WAVE ROVER 参考
上位机 camera 代码在本地 `docs/vendor/waveshare_wave_rover/ugv_rpi/` 下，USB camera
仍按 OpenCV/V4L2 输入源处理；本项目当前实板继续以只读枚举和 `/health` 读回确认
`/dev/video1` 是 DV20 UVC capture。

`onboard/scripts/local_webrtc_camera_smoke.py` 现在把“选到了 video source”和“真的读到首帧”
拆成两个状态：

- `source_readiness=source_selected_not_probed`：只表示已选中 `/dev/video1`，还没有任何
  WebRTC offer 或 MJPEG client 读到真实 frame。
- `source_readiness=first_frame_observed`：只有 WebRTC offer 或 MJPEG stream 成功读到
  frame 后才写入，同时 `/health.last_successful_frame` 会记录 source、channel、宽高和时间。
- `source_readiness=first_frame_failed`：首帧读取失败或超时，仍然 fail closed。

真实上车复测：`GET http://192.168.1.11:8088/health` 返回
`status=ready`、`video_source=/dev/video1`、`source_usage.status=not_in_use`、
`source_readiness=source_selected_not_probed`、`last_successful_frame=null`。这说明当前没有
其它进程独占相机，但也没有证明 DV20 已经出画面；因此不能把该状态用于建图、视觉路线
关键帧或自动扫图运动放行。

## 2026-06-26 共享实时预览与 MJPEG fallback

PC 首屏实时画面现在采用两条只读画面链路：

- 优先自动接入 WebRTC `recvonly` peer；每个进入页面的浏览器都创建自己的 peer。
- 当 WebRTC ICE 已发 offer 但 video 元素仍未绘帧时，PC 页面显示 MJPEG fallback：
  `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787`。

链路为：

```text
PC browser <img>
  -> PC Node /api/robot-control/camera/mjpeg
  -> upper API /api/camera/mjpeg
  -> camera service 8088 /mjpeg
  -> SharedCameraCapture(/dev/video1)
```

`local_webrtc_camera_smoke.py` 的 MJPEG 与 WebRTC 共用 `SharedCameraCapture`：
同一视频源只打开一个 OpenCV `VideoCapture`，每个 WebRTC peer 或 MJPEG HTTP
client 只增加引用计数，最后一个 client 断开后才释放设备。该链路不发布
`/cmd_vel`，不调用底盘串口，不改变 `safe_to_control=false`、
`robot_control_executed=false`。

2026-06-27 17:36 起，MJPEG 首帧 warmup 预算与 WebRTC offer 对齐为 3 秒：
PC 首屏多人共享预览不再使用更短的 1 秒预算提前判定 UVC 无帧。该路径仍必须读到真实
OpenCV 帧才输出 JPEG；读不到帧时继续返回结构化失败，不输出黑帧或 placeholder。

2026-06-27 17:44 起，MJPEG 共享预览额外使用 9 秒首帧总预算。WebRTC offer 仍可跑完整
格式矩阵做深度排障；MJPEG 作为 PC 首屏默认多人预览，在当前 DV20 UVC 无帧形态下会快速返回
`first_frame_total_timeout` / `first_frame_unreadable` JSON 诊断，避免页面长时间停在等待画面。

本轮真机 smoke：

- `GET http://127.0.0.1:8088/mjpeg` 返回 multipart MJPEG，2 秒截取约 526 KB，
  数据包含 `Content-Type: image/jpeg` 与 JPEG SOI `0xffd8`。
- `GET http://127.0.0.1:8787/api/camera/mjpeg` 返回 multipart MJPEG，2 秒截取约
  525 KB。
- `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg?baseUrl=...8787`
  返回 multipart MJPEG，带 `X-Robber-Proxy: camera-mjpeg-readonly`。
- PC 浏览器首屏在未点击“打开画面”的情况下显示 `画面可见`，
  `robot-camera-mjpeg-preview` 为 `640x480`，状态文案为“当前显示 MJPEG 实时画面”。
- 客户端断开 3 秒后，8088 health 显示 `active_peer_count=0`、
  `shared_captures={}`，证明 PC proxy 会随响应关闭 abort 上游流。

当前仍保留 WebRTC 诊断：本轮 in-app browser 中 WebRTC offer 能创建 peer，但 ICE
停在 `new` 且 `frames_read=0`；MJPEG fallback 是为现场实时可视优先提供的稳定通道，
不是运动或视觉算法完成证明。

## 2026-06-26 23:30 camera service 运行形态复查

本轮按真实上位机 `root@192.168.1.11:37878` 复查，当前“摄像头看不到效果”不是多浏览器独占导致：

- `GET http://192.168.1.11:8787/api/camera/health` 显示 `source_usage.other_owner_count=0`，
  `/dev/video1` 没有其它进程占用；发起失败 MJPEG 后也能回到 `shared_captures={}`。
- 当前阻塞是 `/dev/video1` 首帧失败：`source_readiness=first_frame_failed`、
  `source_failure_reason=capture_read_returned_false`、`last_successful_frame=null`。
- `GET http://192.168.1.11:8787/api/camera/mjpeg` 在 5 秒内没有输出真实 JPEG，说明不能把
  2026-06-26 共享 MJPEG 历史 smoke 外推为当前画面可见。
- 8088 端口当前由手工 `python3 scripts/local_webrtc_camera_smoke.py ...` 进程监听，而
  `trashbot-local-webrtc-camera.service=inactive`；这会让共享预览依赖不可复现的现场进程。
- 为避免 systemd `ExecStart=/root/rober/onboard/scripts/local_webrtc_camera_smoke.sh` 指向仓库外遗留脚本，
  `onboard/scripts/local_webrtc_camera_smoke.sh` 已入仓。脚本默认绑定 `0.0.0.0:8088`、`ROBER_CAMERA_SOURCE=auto`，
  只启动 camera smoke，不启动 ROS2、串口、Nav2 或底盘控制。

结论：共享预览链路已经按单上游多客户端设计；当前要让“谁进来都能看到实时预览”真正成立，
必须先恢复由 systemd 管理的 8088 camera service，并解决 DV20 `/dev/video1` 首帧输出问题。

## 2026-06-27 06:06 当前共享预览结论

PC 侧仍按共享预览口径展示摄像头：每个浏览器页面接入自己的 WebRTC peer 或 MJPEG client，
PC Node 对 MJPEG 只维护一条上游流再 fanout，8088 camera service 的 `SharedCameraCapture`
对同一视频源只打开一个 OpenCV `VideoCapture`。因此当前“看不到效果”不能简单归因为页面独占。

真实状态仍是 DV20 `/dev/video1` 首帧失败：summary 读回 `source_first_frame_failed`、
`source_usage_status=not_in_use`、`shared_preview_exclusive_camera_claim=false`。这表示摄像头当前没有被
其它页面抢占，但底层设备没有输出可读视频帧；恢复实时预览需要继续查 DV20 输入、USB 供电、
格式协商或替换 known-good UVC 摄像头验证。本结论不发布 `/cmd_vel`，不调用底盘串口，不改变
`safe_to_control=false`、`robot_control_executed=false`。

## 2026-06-27 12:41 camera no-frame not-exclusive diagnosis

本轮把“看不到实时画面是否因为页面独占”固化为上车端和 PC 端的结构化诊断：

- 8088 `local_webrtc_camera_smoke.py` 的 `/health` 新增 `source_diagnosis`。
  当选中 DV20 `/dev/video1`、最近首帧失败、`source_usage` 显示没有其它进程占用且候选是
  UVC/USB 时，返回 `status=uvc_no_frame_not_exclusive`、`not_exclusive=true`、
  `shared_preview_contract=single_shared_capture_for_multiple_clients`。
- PC summary 透出 `source_diagnosis_status/plain_hint/next_action/not_exclusive`，
  普通用户首屏优先显示“不是页面独占，UVC 没有输出视频帧”，高级诊断保留机器可读字段。
- 本轮不启动 Nav2、不调用 `/api/base/manual`、不发布 `/cmd_vel`、不写 WAVE ROVER UART。
  它只让相机故障更可解释；真正恢复实时预览仍需要检查 USB、摄像头输入、供电或换 known-good
  UVC 摄像头复测。

真实上位机部署后，`GET http://192.168.1.11:8088/health` 读回：
`status=source_first_frame_failed`、`source_usage.status=not_in_use`、
`source_diagnosis.status=uvc_no_frame_not_exclusive`、`source_diagnosis.not_exclusive=true`。
PC 7001 summary 同步读回 `shared_preview_exclusive_camera_claim=false` 和
`source_diagnosis_plain_hint=不是页面独占...UVC 设备没有输出视频帧...`。

## 2026-07-01 00:52 camera service restart 与 STREAMON 证据

本轮继续按真实上位机 `root@192.168.1.11:37878` 复查摄像头链路，结论仍是“8088 共享预览服务可用，但
DV20 `/dev/video1` 没有输出 kernel frame”，不是浏览器独占：

- 现场发现旧 `python3 scripts/local_webrtc_camera_smoke.py ...` 进程脱离 systemd 后仍监听 `0.0.0.0:8088`，
  导致 `trashbot-local-webrtc-camera.service` 重启时反复报 `OSError: [Errno 98] Address already in use`。
  `onboard/scripts/local_webrtc_camera_smoke.sh` 已新增 stale listener 清理：只杀同端口且命令行包含
  `local_webrtc_camera_smoke.py` 的旧实例；如果端口被其它服务占用，只报错不抢占。
- 上车部署后连续两次 `systemctl restart trashbot-local-webrtc-camera.service` 均成功，
  `systemctl is-active` 为 `active`，8088 由 systemd MainPID 监听。
- 共享 MJPEG 复测后，`GET http://127.0.0.1:8088/health` 返回
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=first_frame_total_timeout`、`source_usage.status=not_in_use`、
  `source_diagnosis.status=uvc_no_frame_not_exclusive`。
- `camera_first_frame_probe.py --include-backend-smoke` 现在即使 OpenCV `open_failed` 也会继续跑
  V4L2/ffmpeg backend smoke，并汇总 `streamon_io_error_observed/count/latest_streamon_io_error`。
  现场读回 `streamon_io_error_observed=true`、`streamon_io_error_count=9`，最新错误为
  `ioctl(VIDIOC_STREAMON): Input/output error` / `/dev/video1: Input/output error`。

本轮修复的是 8088 service 可重复恢复和 PC/脚本对底层无帧根因的所见即所得表达；没有证明摄像头已可见。
恢复画面仍需检查 USB 线/接口/供电、DV20 输入，或替换 known-good UVC 后复测。

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

## 2026-06-11 21:20 reproducible first-frame probe tool

`sprints/2026.06.11_21-20_camera_first_frame_probe_tool/` 新增
`onboard/scripts/camera_first_frame_probe.py`，把之前临时 SSH 里的 OpenCV
首帧读取逻辑沉淀成可复用工具。资料入口仍以 `docs/vendor/VENDOR_INDEX.md`
为准；本工具只触碰 UVC/V4L2 camera path，不写 WAVE ROVER UART，不调用
`/api/base/manual`，不发布 `/cmd_vel`。

典型用法：

```bash
python3 /root/rober/onboard/scripts/camera_first_frame_probe.py \
  --device /dev/video1 \
  --width 640 \
  --height 480 \
  --fps 15 \
  --fourcc MJPG \
  --timeout-s 3 \
  --read-call-timeout-s 4 \
  --sample-path /tmp/rober-camera-first-frame.jpg
```

输出是单行 JSON，schema 为 `trashbot.camera_first_frame_probe.v1`。关键字段：

- `status=dependency_missing|open_error|open_failed|first_frame_timeout|probe_error|frame_read`
- `open_ok`、`read_ok`、`first_frame_timeout`、`failure_reason`、`attempts`、`elapsed_ms`
- `timeout_s` 与 `read_call_timeout_s`，用于区分整体 deadline 和单次 `cap.read()` 阻塞
- `frame_metrics.mean_luma`、`dynamic_range_luma`、`non_black_ratio`
- `frame_metrics.visible_content_candidate`
- `visible_content_proven=false`

这里刻意保留 `visible_content_proven=false`：脚本读到一帧只能证明本机 camera
首帧通路恢复，并给出图像质量候选；运动 HIL gate 仍需要 PC canvas/外部视频、
轮速反馈非零和 LiDAR motion delta 共同证明。

## 2026-06-11 22:00 PC-triggered first-frame probe

`sprints/2026.06.11_22-00_pc_camera_first_frame_probe_proxy/` 将同一个首帧探针接入
上位机 API 和 PC 高级诊断：

- 上位机：`POST /api/camera/first-frame/probe`
- PC proxy：`POST /api/robot-control/camera/first-frame/probe?baseUrl=...`
- PC UI：默认关闭的 `高级诊断 / 实时画面详情 / 首帧探针（高级）`

真实 PC proxy smoke 仍显示 `/dev/video1` 为当前源，`requested_fourcc=MJPG`、
`open_ok=true`、`read_ok=false`、`first_frame_timeout=true`、
`failure_reason=capture_read_call_timeout`、`visible_content_proven=false`。因此本轮只让
PC 页面获得了可重复触发的底层相机诊断闭环，没有恢复实时图传可见内容。

## 2026-06-11 23:05 camera source readiness refresh

`sprints/2026.06.11_23-05_camera_source_auto_probe_refresh/` 在真实上位机
`root@192.168.1.11:37878` 上重新枚举 `/dev/video*` 并跑 `camera_first_frame_probe.py`
矩阵。资料入口仍以 `docs/vendor/VENDOR_INDEX.md` 为准；本轮只触碰 UVC/V4L2 camera
链路，不写 WAVE ROVER UART，不调用 `/api/base/manual`，不发布 `/cmd_vel`。

真实设备枚举保持不变：`/dev/video0` 是 `cedrus (platform:cedrus)` decoder，
`/dev/video1` 是 DV20 USB `Video Capture`，`/dev/video2` 是同一 DV20 的 metadata
节点。首帧矩阵结论是 `/dev/video1` 可 open，但 default、`MJPG 640x480` 与
`YUYV 640x480` 均 `read_ok=false`、`first_frame_timeout=true`、
`failure_reason=capture_read_call_timeout`；`/dev/video0` 和 `/dev/video2` 均不可作为
图像源打开。

`onboard/scripts/local_webrtc_camera_smoke.py` 的 `/health` 因此新增只读字段
`source_readiness` 与 `source_failure_reason`。未发 offer 时，选到 `/dev/video1`
会显示 `source_readiness=source_selected_not_probed`；真实 aiortc offer 触发首帧失败后，
同一服务会显示 `status=source_first_frame_failed`、
`source_readiness=first_frame_failed`、`source_failure_reason=first_frame_timeout`。
这只是让状态从“源已选择”变成“源首帧失败”的诚实诊断，不代表实时图传可见内容恢复。

## 2026-06-11 23:45 camera service supervisor recapture

`sprints/2026.06.11_23-45_live_evidence_status_recapture/` 发现真实上位机
`trashbot-local-webrtc-camera.service` 处于 `inactive`，但 8088 仍由手工残留进程
`python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py ...` 提供。这会让 PC
实时图传依赖不可重复的 orphan process。

本轮先记录该状态，再停止手工进程并通过 systemd 重新启动
`trashbot-local-webrtc-camera.service`。最终状态：

- `trashbot-upper-robot-api.service=active`
- `trashbot-local-webrtc-camera.service=active`
- 8088 由 systemd 管理的 `local_webrtc_camera_smoke.py` 进程监听。
- `/health` 重新选择 `/dev/video1`，初始为 `source_selected_not_probed`。
- 对 systemd 管理进程发起真实 aiortc offer 后，仍返回 HTTP 503
  `first_frame_unreadable/first_frame_timeout`，并把 `/health` 标回
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=first_frame_timeout`。

这次修复的是 camera service 运行形态和可重复性，不是 `/dev/video1` 首帧问题本身。
`visible_content_proven=false` 仍成立。

## 2026-06-12 camera backend capture matrix

`sprints/2026.06.12_01-15_camera_backend_capture_matrix/` 继续在真实上位机
`root@192.168.1.11:37878` 上排查 DV20 `/dev/video1` 首帧失败。本轮先停止
`trashbot-local-webrtc-camera.service`，确认 `/dev/video0/1/2` 和 `/dev/ttyS5`
无 holder，再分别用 OpenCV、`v4l2-ctl` 和 `ffmpeg` 取首帧。

结果：

- `/dev/video1` 仍是 `USB Composite Device: DV20 USB` 的 `Video Capture` 节点。
- `v4l2-ctl --all -d /dev/video1` 显示 input ok，支持 `MJPG` 与 `YUYV`。
- `v4l2-ctl` default、`MJPG 640x480`、`YUYV 640x480` 的 stream 输出均为 0 bytes。
- `ffmpeg -f v4l2 -input_format mjpeg` 和 `yuyv422` 均没有写出 frame。
- 上位机 `POST /api/camera/first-frame/probe` 新增 `include_backend_smoke=true`
  后回报 `backend_smoke.status=backend_no_frame_observed`、`frame_observed=false`。
- PC 高级诊断同一路径回报 `backend_smoke_status=backend_no_frame_observed`、
  `backend_frame_observed=false`、`backend_attempts=4`。

这说明当前 blocker 不只是 WebRTC 或 OpenCV：同一 DV20 设备在底层 V4L2/ffmpeg
路径也没有实际帧输出。下一步应检查 DV20 输入源、HDMI/USB 线缆、供电和采集卡状态，
或替换 known-good UVC 后用同一 PC 高级按钮复测。

证据文件：

- `sprints/2026.06.12_01-15_camera_backend_capture_matrix/artifacts/01_board_camera_backend_matrix.log`
- `sprints/2026.06.12_01-15_camera_backend_capture_matrix/artifacts/02_upper_camera_probe_backend_smoke.json`
- `sprints/2026.06.12_01-15_camera_backend_capture_matrix/artifacts/03_pc_proxy_camera_probe_backend_smoke.json`

## 2026-06-12 02:50 PC full sweep camera status

`sprints/2026.06.12_02-50_pc_full_safe_evidence_sweep/` 复用 PC fixed proxy
`POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787`
再次确认真实上位机 camera 状态。本轮没有触碰底盘运动、Nav2 执行或 `/cmd_vel`。

结果保持为硬件输入层 blocker：

- `remote_http_status=503`
- `status=first_frame_timeout`
- `failure_reason=capture_read_call_timeout`
- `device=/dev/video1`
- `open_ok=true`
- `read_ok=false`
- `visible_content_proven=false`
- `backend_smoke.status=backend_no_frame_observed`

这与上一轮 V4L2/ffmpeg backend matrix 一致：PC、WebRTC 和 OpenCV 之外的底层后端也没有
观察到实际帧。下一步仍应优先检查 DV20 输入源、HDMI/USB 线缆、供电、采集卡，或替换
known-good UVC 后复测；不能把 `/api/camera/health ready` 当成可见图传验收。

## 2026-06-22 first-frame visible sample artifact

`sprints/2026.06.22_01-10_camera_visual_material_probe/` 修复了 camera first-frame
probe 的证据闭环：`camera_first_frame_probe.py` 只有在 `visible_content_candidate=true`
且样张文件写入成功时，才把 `visible_content_proven=true` 写入 probe payload。
`upper_robot_api.py` 调用该 probe 时会固定传入
`/root/rober/onboard/runtime/camera/first_frame_probe_<timestamp>.jpg`，避免只有亮度指标、
没有可追溯样张的状态被误当成 first-jog 视觉材料。

真实上位机 `root@192.168.1.11:37878` / Robot API `http://192.168.1.11:8787`
本轮实测：

- 直连 `/api/camera/first-frame/probe` 返回 `status=frame_read`、
  `open_ok=true`、`read_ok=true`、`sample_write_ok=true`、
  `visible_content_candidate=true`、`visible_content_proven=true`。
- PC 代理 `/api/robot-control/camera/first-frame/probe` 返回
  `proxy_status=probe_forwarded`、`remote_http_status=200`，并透出样张路径
  `/root/rober/onboard/runtime/camera/first_frame_probe_1782060889824.jpg`。
- 本轮没有把相机可见样张解释成路线关键帧、视觉定位、障碍识别或交付成功；
  它只满足 first-jog 的 `external_video_or_visible_camera` 前置材料。

## 2026-06-22 stale peer release before first-jog visual material

本轮复测 PC first-jog 前置视觉材料时，`/api/camera/first-frame/probe` 一度返回
HTTP 503 `open_failed`。排查发现 `/dev/video1` 被 stale WebRTC peer
`f040d79c10d4` 持有，peer 已存在约 9 小时且 `frames_read=0`。通过 PC proxy 调用
`POST /api/robot-control/camera/peers/f040d79c10d4/close` 后，重新执行
first-frame probe 得到：

- `remote_http_status=200`
- `status=frame_read`
- `visible_content_proven=true`
- `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782096252146.jpg`
- `mean_luma=7.7865`
- `dynamic_range_luma=48.983`
- `non_black_ratio=0.190534`

这份样张随后作为 operator report `evidence_ref=first-jog-visual-1782096252146`
的视觉材料，使 first-jog readiness 从缺少视觉材料推进到 `ready_for_first_jog`。
该材料仍只证明当前相机链路有可见样张，不证明检测、定位、避障、完整路线或交付成功。

## 2026-06-26 PC camera gate 同步

PC 普通首屏现在把上位机 camera health 的首帧失败原因统一纳入共享预览和建图门禁：
`source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`
或 `capture_read_call_timeout` 都会显示为“相机没有出画面，检查摄像头/视频线”，并阻止 `扫地式建图` 调用
`/api/robot-control/map/start`。这只是把真实采集失败 fail-closed 地暴露给 operator，不会自动打开摄像头、不发送
manual/keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。

当前真实上位机仍可能返回 `/dev/video1` 已选择但 `capture_read_returned_false`。该状态表示底层 V4L2/OpenCV
没有拿到实际帧，仍需现场检查摄像头、线缆、供电、采集卡或替换 known-good UVC 后复测；不能把设备路径存在解释成画面可用。

## 2026-06-26 19:42 camera source usage 诊断

上车端 `local_webrtc_camera_smoke.py` 的 `/health` 新增只读 `source_usage`：

- 扫描 `/proc/*/fd` 判断当前选中的 `/dev/video*` 是否被本服务、probe、`v4l2-ctl`、`ffmpeg` 或其它进程持有。
- 该诊断固定 `opens_camera=false`，不会通过 OpenCV 或 V4L2 打开摄像头，也不会写 V4L2 control。
- PC summary 会透出 `camera_source_usage_status`、`camera_source_usage_owner_count` 和短摘要。
- 普通首屏在首帧失败时会区分“相机被进程占用”和“没人占用但底层无帧”。后者说明问题更接近 USB/输入/供电/采集卡，而不是页面独占。

本轮仍不把 `source_usage=not_in_use` 当作图传可用；真实可见画面仍必须由 WebRTC/MJPEG 像素绘制或 first-frame 样张证明。

## 2026-06-26 20:30 backend smoke release-before-probe

`camera_first_frame_probe.py --include-backend-smoke` 现在会在 OpenCV 首帧失败后先释放 `VideoCapture`，
再运行 `v4l2-ctl` / `ffmpeg` 后端矩阵。这样后端矩阵看到的 `Device busy` 不再来自探针自身残留的 OpenCV 句柄，
更适合判断问题到底在 OpenCV、V4L2、采集卡输入还是硬件链路。

真实上位机 `root@192.168.1.11:37878` 复测结果：

- OpenCV 可打开 `/dev/video1`，但 `read_ok=false`，`failure_reason=capture_read_call_timeout`。
- 释放 OpenCV 后，`v4l2_mjpg_mmap`、`v4l2_yuyv_mmap`、`ffmpeg_mjpg`、`ffmpeg_yuyv` 均按超时结构化返回，
  `frame_observed=false`，不再被探针自身占用误报为 busy。
- camera service 已恢复运行，Robot API 仍保持 `safe_to_control=false`、`primary_actions_enabled=false`。

该证据把当前相机问题进一步收敛到“设备可枚举但实际无帧输出/输入链路异常”，不能通过 PC 侧共享预览代码绕过。

## 2026-06-26 22:45 camera service `/api/camera/*` alias

上车端 `local_webrtc_camera_smoke.py` 现在同时兼容历史根路径和 Robot API 风格路径：

- `GET /health` 与 `GET /api/camera/health` 等价。
- `GET /devices` 与 `GET /api/camera/devices` 等价。
- `GET /mjpeg` 与 `GET /api/camera/mjpeg` 等价。
- `POST /offer` 与 `POST /api/camera/offer` 等价。
- `POST /peers/{peer_id}/close` 与 `POST /api/camera/peers/{peer_id}/close` 等价。

这样 operator 或 PC/上位机代理无论走 8088 直连还是 8787 `/api/camera/*`
合同，都能看到同一 camera service 状态，不会再因为路径漂移得到
`unknown_get_endpoint`。该别名层只改 HTTP 路由归一化，不打开底盘、不启动雷达、
不调用 Nav2、manual、keyboard、delivery、free-roam start/stop 或 `/cmd_vel`。

同轮还修正了首帧失败路径的清理：如果 MJPEG/WebRTC 在 MJPG、YUYV 和默认格式尝试后
仍读不到首帧，已经 `force_release` 的 shared capture 会从 health 摘要中移除；
客户端提前断开时只记录 `json_response_client_disconnected` 短事件，不再输出
BrokenPipe 栈。

真实上位机复测：

- `http://127.0.0.1:8088/api/camera/health`：HTTP 200，
  `schema=trashbot.local_webrtc_camera_smoke.v1`。
- `http://127.0.0.1:8088/api/camera/devices`：HTTP 200，
  `schema=trashbot.local_webrtc_camera_devices.v1`。
- `http://127.0.0.1:8787/api/camera/health` 与
  `/api/camera/devices`：均 HTTP 200。
- 触发 `/api/camera/mjpeg` 后，最终 health 回到
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=capture_read_returned_false`、
  `source_usage.status=not_in_use`、`shared_captures={}`。

剩余事实没有改变：`/dev/video1` 能枚举并被选中，但仍没有输出可见视频帧；
这不是 PC 页面独占导致，下一步仍应查摄像头输入、USB 线/供电、采集卡或替换
known-good UVC。

## 2026-06-27 USB reset 后端复测

在 `root@192.168.1.11 -p 37878` 上继续排查 DV20：

- `v4l2-ctl -d /dev/video1 --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap=3 --stream-count=1`
  和 YUYV 组合均只写出 0 字节 raw。
- 修正参数顺序后的 `ffmpeg -f v4l2 -input_format mjpeg/yuyv422 -video_size 640x480 -i /dev/video1 -frames:v 1`
  均未写出 JPEG；MJPG 在 EOF 前不能确定像素格式，YUYV 输出 0 帧。
- 停止 `trashbot-local-webrtc-camera.service` 后，对 USB 设备 `3-1` 执行 unbind/bind，DV20 重新枚举，
  `/dev/video1` 时间戳刷新，camera service 可重新 active。
- reset 后 `GET /mjpeg` 仍返回 503，body 中六种 OpenCV 尝试均为 `capture_read_returned_false`。
- reset 后固定 `POST /api/camera/first-frame/probe` 且 `include_backend_smoke=true` 返回
  `first_frame_timeout/capture_read_call_timeout`，backend smoke 的 `v4l2_mjpg_mmap`、`v4l2_yuyv_mmap`、
  `ffmpeg_mjpg`、`ffmpeg_yuyv` 全部 timeout，`output_bytes=0`。

结论：本轮已排除 PC 多浏览器独占、8088 OpenCV 单一路径和一次 USB 重新枚举可恢复这三个方向。当前剩余问题在
DV20 输入源、采集卡工作模式、USB 线/供电或设备本体；软件只能继续 fail-closed 展示“无真实首帧”，不能提供假预览或把
`/dev/video1` 存在当成建图 ready。

## 2026-06-27 06:28 source_not_probed WYSIWYG 收口

真实上位机 `root@192.168.1.11 -p 37878` 再次按同一路径复测：

- 停止 8088 camera service 后，对 Orange Pi USB 设备 `3-1` 执行
  `/sys/bus/usb/drivers/usb/{unbind,bind}`，`/dev/video1` 与 `/dev/video2`
  重新枚举，时间戳刷新到 `2026-06-27 06:24`。
- 重启 `local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`
  后，8088 与 8787 均恢复监听。
- `v4l2-ctl -d /dev/video1 --stream-mmap=3 --stream-count=3` 仍 8 秒超时，
  输出文件 0 字节。
- `POST http://127.0.0.1:8787/api/camera/first-frame/probe` 仍返回
  `status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`。

因此本轮新增的是 PC 口径收紧：`source_readiness=source_selected_not_probed`
不再在 Robot Control summary 中冒充 `status=ready`，而是显示为
`status=source_not_probed`。普通首屏对应显示“相机在线但还没确认首帧”，避免
8088 重启后只因选中了 `/dev/video1` 就把画面误判为 ready。

## 2026-06-27 03:20 systemd active 但 UVC 内核层无帧

按 `docs/vendor/VENDOR_INDEX.md` 的硬件资料入口要求，本轮先确认本项目硬件栈仍以
Orange Pi Zero 3 作为上位机入口；DV20 USB 摄像头不是 vendor 目录中已有细化资料项，
因此本节只采用实板 `v4l2-ctl`、systemd 和 HTTP readback 证据，不猜测摄像头内部协议。

真实上位机 `root@192.168.1.11 -p 37878` 复查结果：

- `trashbot-local-webrtc-camera.service` 已 `active (running)`，命令行为
  `local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`。
- `0.0.0.0:8088` 与 `0.0.0.0:8787` 均有 Python 服务监听；没有发现其它明显 camera owner。
- `v4l2-ctl --list-devices` 仍显示 `/dev/video0` 是 Cedrus decoder，`/dev/video1`/`/dev/video2`
  属于 `USB Composite Device: DV20 USB`。
- `/dev/video1 --all` 显示 `Driver name: uvcvideo`、`Video Capture`、`Streaming`，
  当前输入状态为 `Input 1: ok`。
- `/dev/video1 --list-formats-ext` 显示 MJPG 支持 `640x480@30`、`1280x720@30` 等，
  YUYV 支持 `640x480@22`、`320x240@25/20`。
- 但 `v4l2-ctl -d /dev/video1 --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap=3 --stream-count=1`
  和 YUYV 组合均超时，输出 raw 文件为 0 字节。
- 通过 `8787` 转发读取 `GET /api/camera/mjpeg` 同样超时，没有 JPEG header 或 body。

结论保持 fail-closed：共享预览/多浏览器访问路径已由 8088 camera service 承担，当前失败不应再归因于
PC 页面独占；更接近 DV20/UVC 设备枚举正常但内核 streaming 不产出帧。下一步应现场检查 USB 供电、
摄像头输入源/模式、线缆或替换 known-good UVC。软件侧新增的 backend smoke 会继续把
`no_frame_timeout`、0 字节和 `no_kernel_frame_observed` 展示给 PC，而不会伪造预览、解锁建图 ready
或发送任何运动命令。

## 2026-06-27 10:16 PC 普通首屏 OpenCV/V4L2 无帧提示

在 `root@192.168.1.11 -p 37878` 上复核当前 live 摄像头链路：

- `GET /api/camera/health` 仍显示 `/dev/video1` 被选为
  `USB Composite Device: DV20 USB`，`source_readiness=first_frame_failed`，
  `source_failure_reason=capture_read_returned_false`，`source_usage.status=not_in_use`，
  `owner_count=0`。
- 顺序执行 `v4l2-ctl` 对 `/dev/video1` 采 `YUYV 640x480` 与 `MJPG 640x480`
  均 10 秒超时，输出 raw 文件为 0 字节；前后 `fuser /dev/video1 /dev/video2`
  无占用输出。
- 通过 PC Node 固定探针
  `POST /api/robot-control/camera/first-frame/probe?backendSmoke=1`
  返回 `proxy_status=probe_failed`、`status=first_frame_timeout`、
  `open_ok=true`、`read_ok=false`、`backend_smoke_status=backend_no_frame_observed`、
  `backend_attempts=4`。

PC 普通首屏因此把失败提示改为“不是页面独占，摄像头能打开，OpenCV/V4L2
后端尝试多种方式也没有取到视频帧”。这条文案明确区分浏览器/WebRTC/多人预览
fanout 与上车端底层采集无帧；仍不把 `/dev/video1` 可枚举或 camera service
active 当作画面 ready，也不会解锁建图验收。

## 2026-06-27 10:45 systemd 托管恢复但首帧仍失败

按 `docs/vendor/VENDOR_INDEX.md` 的硬件资料入口要求，本轮仍以本地资料中的
Orange Pi Zero 3 + WAVE ROVER 上位机链路为边界；本节只记录相机 HTTP 服务、
V4L2 设备和只读首帧探针，不发布 `/cmd_vel`，不访问 WAVE ROVER UART。

真实上位机 `root@192.168.1.11 -p 37878` 复查并恢复运行形态：

- 8088 曾由手工 `python3 scripts/local_webrtc_camera_smoke.py ...` 进程占用，
  导致 `trashbot-local-webrtc-camera.service` 进入 auto-restart；切回后
  `trashbot-local-webrtc-camera.service=active`，8088 由
  `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 监听。
- 8787 也曾被旧 upper API 进程占用，导致 `trashbot-upper-robot-api.service`
  auto-restart；停止旧监听 PID 后重启服务，最终
  `trashbot-upper-robot-api.service=active`，8787 由
  `/root/rober/onboard/scripts/upper_robot_api.py` 监听。
- `GET /api/camera/health` 在重启后先回到
  `status=ready`、`source_readiness=source_selected_not_probed`、`selected_path=/dev/video1`、
  `source_usage.status=not_in_use`，说明服务托管和自动选源恢复。
- 通过 PC 7001 固定首帧探针再次打开摄像头后，summary 仍显示
  `source_first_frame_failed`、`first_frame_probe_status=first_frame_timeout`、
  `first_frame_probe_failure_reason=capture_read_call_timeout`、
  `first_frame_probe_open_ok=true`、`first_frame_probe_read_ok=false`、
  `first_frame_probe_backend_smoke_status=backend_no_frame_observed`。
- PC 7001 live summary 同时显示
  `shared_preview_exclusive_camera_claim=false`、`source_usage_status=not_in_use`、
  `shared_preview_client_count=0`，因此当前看不到画面不是 PC 页面独占。

结论：共享预览服务现在应由 systemd 稳定托管，支持多人通过同一 8088/8787/7001
链路进入实时预览；但 DV20 `/dev/video1` 仍是“能打开、不能读首帧”。软件侧必须继续
fail-closed，把建图缺口保留为 `camera_first_frame`，不能因为服务 active 或设备枚举正常
就宣称画面可用。

2026-06-27 14:52 起，PC 普通首屏共享预览文案进一步按失败事实收口：当 summary 或
`/api/robot-control/camera/mjpeg/status` 已明确 `camera_source_first_frame_failed`、
`camera_mjpeg_upstream_timeout`、HTTP 5xx 或 health 首帧失败时，状态行不再写
`页面正在接入共享预览`。这样 live 的“0 个页面观看、上游未连接、不是独占、UVC 无首帧”
不会被误解成仍在加载；只有相机 ready 且无已知失败时才显示正在接入共享预览。
该调整只影响 PC 文案，不打开额外摄像头、不运行首帧探针、不发布运动命令。

## 2026-06-27 15:37 MJPEG status selected-source diagnosis

PC `GET /api/robot-control/camera/mjpeg/status` 继续保持只读、不会创建 MJPEG client；但现在会把
上车 `/api/camera/health` 里的 `source_not_probed/source_selected_not_probed` 诊断同步贴到 status。

## 2026-07-01 02:20 UVC 内核传输错误 WYSIWYG 诊断

真实上车环境里 `/dev/video1` 仍能枚举为 `USB Composite Device: DV20 USB`，但 `dmesg`
已有 `error -71`、`Failed to initialize the device`、`Failed to resubmit video URB`、
`can't read configurations` 等 UVC/USB 传输错误。旧版 8088 camera smoke 只扫 `dmesg`
短 tail，服务轮询日志变多后会把这些旧 UVC 错误挤出窗口，导致 health 误报
`uvc_kernel_log_not_matched`。

`onboard/scripts/local_webrtc_camera_smoke.py` 现在全量扫描 `dmesg`，但只在响应里返回截断
tail；并从 `uvcvideo 3-1` / `usb 3-1` 日志提取同一个内核 USB 地址，把后续同地址
`error -71` 或配置读取失败归到当前 UVC 摄像头。该诊断仍然只读内核日志和 v4l2 枚举，
不会打开额外 camera reader、不会 reset USB、不会启动 ROS2，也不会发布 `/cmd_vel`。

部署到 `root@192.168.1.11:37878` 后，`/api/camera/health` 已返回：

- `source_diagnosis.status=uvc_transport_error_not_exclusive`
- `uvc_kernel_diagnostics.status=uvc_usb_transport_errors_observed`
- `uvc_kernel_diagnostics.transport_error_count=44`
- `latest_transport_error=[777992.581028] usb 3-1: device descriptor read/all, error -71`

PC 7001 的 `/api/robot-control/camera/mjpeg/status` 和 `/api/robot-control/summary`
同步显示中文下一步：检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；
共享预览不是页面独占。该结论推进“画面所见即所得”：当前不是页面抢占或多用户预览独占，
而是 UVC/USB 链路已经有内核传输错误，仍未证明真实画面可见。

live 只读复核：

- `client_count=0`
- `upstream_active=false`
- `shared_capture=true`
- `exclusive_camera_claim=false`
- `source_diagnosis_status=source_selected_not_probed`
- `source_diagnosis_not_exclusive=true`
- `source_diagnosis_next_action=open_shared_preview_or_run_first_frame_probe`

这表示新进入的页面即使还没有打开共享预览，也能看到“已选中 DV20 `/dev/video1`、不是页面独占、下一步打开共享预览或首帧检查”。
该 status 查询不打开相机 reader、不触发首帧探针、不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

## 2026-06-28 09:50 first_frame_total_timeout 非独占诊断

本轮只读复核真实上位机 `root@192.168.1.11 -p 37878`，只请求 GET：

- `/api/camera/health` 返回 `status=source_first_frame_failed`、
  `source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`。
- 同轮 `/api/radar/status` 返回 `lifecycle_running=false`、`lifecycle_state=stopped`；
  `/api/free-roam/autonomy/latest` 与 `/api/nav2/status` 仍是 `not_proven`。

PC Node 现在会在 camera health 没有显式 `source_diagnosis`、但读到“首帧失败 + 摄像头无人占用”
时派生 `source_diagnosis_status=uvc_no_frame_not_exclusive`，并把建图 gate 里的
`camera_first_frame` 同步标成“画面首帧未出，不是页面独占”。PC 普通首屏对旧 summary
形状也会把 `first_frame_total_timeout` 翻成“读取首帧总超时”，避免现场继续排查浏览器独占。

这个改动只修只读诊断和文案，不打开额外摄像头 reader，不启动雷达，不执行 Nav2，不发送
manual/free-roam/keyboard/delivery/stop 或 `/cmd_vel`。真实摄像头仍需检查 USB、摄像头输入、
格式、供电或替换 known-good UVC 后复测。

## 2026-06-29 18:29 backend low-load first-frame matrix

当前真实上位机读回仍显示 `/dev/video1` 是 DV20 UVC capture，`/dev/video2` 是 metadata，
且 `source_usage.status=not_in_use`，因此“看不到画面”不是 PC 页面独占，也不是多用户共享预览
设计导致的独占占用。阻塞仍是 UVC 能枚举、能被选中，但首帧没有从驱动/设备侧出来。

`onboard/scripts/camera_first_frame_probe.py` 的 `--include-backend-smoke` 现在除了固定
`MJPG/YUYV@请求尺寸` 外，还会：

- 读取 `v4l2-ctl --list-formats-ext` 的完整输出并解析设备自报格式；
- 额外尝试一次不改格式的 `v4l2_current_mmap`，用于验证当前默认格式是否能直接吐帧；
- 从设备支持列表中选择最多 2 个低分辨率 `MJPG/YUYV` 模式，例如现场 DV20 暴露的
  `MJPG@480x320` 与 `YUYV@320x240`，分别用 `v4l2-ctl` 和 `ffmpeg` 取一帧。

该矩阵仍然只读摄像头，不写 V4L2 controls，不执行 USB reset，不发布 `/cmd_vel`，
也不会把 `safe_to_control` 或 `robot_control_executed` 升级为 true。它的目标是：
如果低负载模式能读到帧，就形成更直接的可见画面恢复证据；如果仍然 0 字节或超时，
就把故障进一步收敛到 DV20/USB/输入源/供电或摄像头本体，而不是 PC 页面或 MJPEG 多用户共享。

部署到 `root@192.168.1.11:37878` 后，通过 8787 API 只读执行
`/api/camera/first-frame/probe`，请求 `include_backend_smoke=true`。结果：

- OpenCV probe：`open_ok=true`、`read_ok=false`、`status=first_frame_timeout`、
  `failure_reason=capture_read_call_timeout`。
- backend smoke：共 9 个尝试，包含原固定 `v4l2_mjpg_mmap`、`v4l2_yuyv_mmap`、
  `ffmpeg_mjpg`、`ffmpeg_yuyv`，新增 `v4l2_current_mmap`、
  `v4l2_device_mjpg_480x320_mmap`、`ffmpeg_device_mjpg_480x320`、
  `v4l2_device_yuyv_320x240_mmap`、`ffmpeg_device_yuyv_320x240`。
- 9 个尝试全部为 `no_frame_timeout`，`output_bytes=0`，`jpeg_soi_observed=false`。
- 复核 `/api/camera/health`：`source_usage.status=not_in_use`、`owner_count=0`、
  `source_diagnosis.status=uvc_no_frame_not_exclusive`。

因此本轮现场结论是：共享预览入口可以多人共用，但当前 DV20 仍没有输出任何可读视频帧；
自动驾驶/建图仍不能依赖摄像头画面，下一步应检查或更换摄像头/USB/供电/输入源。

## 2026-06-27 15:05 camera health ready 收紧

本轮继续只读复核真实上位机 camera 链路：

- `/dev/video1` 仍是 `USB Composite Device: DV20 USB` 的 UVC capture 节点，`/dev/video2` 是 metadata。
- `lsof /dev/video*` 为空，说明当前没有其它进程长期独占摄像头。
- `v4l2-ctl` 分别用 `MJPG@640x480` 和 `YUYV@640x480` 拉一帧，输出文件都是 0 字节。
- OpenCV 对 default、`MJPG@640x480`、`YUYV@640x480`、`YUYV@320x240` 四种模式均 `opened=false`。

因此当前“看不到画面”不能归因成 PC 页面独占或多用户共享设计失效；真实阻塞仍是 DV20 UVC 没有输出可读视频帧。
为避免相机服务重启后仅因选中 `/dev/video1` 就把 health 顶层状态写成 `ready`，
`local_webrtc_camera_smoke.py` 已收紧状态口径：只有 `last_successful_frame` 证明同一 source 已读到真实帧时才返回
`status=ready`；只选中设备但还没读到首帧时返回 `status=source_not_probed`、`source_readiness=source_selected_not_probed`。
该改动不打开底盘、不发布 `/cmd_vel`、不调用 `/api/base/manual`，只修正 camera WYSIWYG 状态。

## 2026-07-01 05:25 UVC full-speed USB topology diagnosis

本轮继续只读复核真实上位机 `root@192.168.1.11 -p 37878`，不执行 Nav2、manual、keyboard、
free-roam、map start、delivery、stop 或 `/cmd_vel`。

采用的本地硬件资料入口是 `docs/vendor/VENDOR_INDEX.md`。其中 Orange Pi Zero 3 用户手册覆盖
USB 接口、USB 摄像头和 5V/2A 或 5V/3A Type-C 供电说明；Orange Pi Zero 3 电路图覆盖
USB DM/DP/VCC_USB 等 USB 相关信号。结论仍以现场 Linux 读回为准。

现场只读证据：

- PC `POST /api/robot-control/camera/first-frame/probe` 返回 HTTP 502，未能形成首帧 JSON 成功证据。
- `GET /api/robot-control/camera/mjpeg/status` 返回 `status=waiting_for_first_frame`、
  `upstream_active=true`、`client_count=1`、`has_recent_frame=false`、
  `last_failure_reason=mjpeg_auto_retry_cooldown_after_first_frame_failure`，且
  `shared_preview_exclusive_camera_claim=false`。
- SSH 上车 `ls -l /dev/video*` 显示 `/dev/video1` 与 `/dev/video2`；`fuser -v /dev/video*`
  无占用输出，说明不是其它进程长期独占。
- `v4l2-ctl --list-devices` 显示 `USB Composite Device: DV20 USB` 对应 `/dev/video1` 和
  `/dev/video2`；`/dev/video1` 具备 Video Capture，支持 `MJPG` 与 `YUYV`。
- `lsusb -t` 显示该 UVC Video 接口当前在 `Bus 06 ... ohci-platform ... 12M` 下：
  `Class=Video, Driver=uvcvideo, 12M`。这意味着摄像头视频链路落到了 full-speed USB，而不是
  high-speed USB。
- 上车短取帧 smoke 到 `/dev/null`：`YUYV@320x240` 与 `MJPG@640x480` 均返回
  `VIDIOC_STREAMON returned -1 (Input/output error)`。
- `dmesg` 有 `device descriptor read/all, error -71`、`Failed to resubmit video URB (-1)`、
  `Failed to query ... UVC probe control : -71` 等 UVC/USB 错误。

代码侧已把这个根因结构化：

- `local_webrtc_camera_smoke.py` 新增 `uvc_usb_topology`，只读 `lsusb -t`，不打开摄像头。
- 当 UVC Video 接口落在 `12M` full-speed 时，`source_diagnosis.status` 可提升为
  `uvc_full_speed_usb_not_exclusive`，`next_action=move_camera_to_high_speed_usb_port_or_powered_hub`。
- `upper_robot_api.py` 将 `uvc_usb_topology_*` 平铺到 8787 camera health / MJPEG status。
- PC summary 继续把字段同步到 `readback_summary.camera.uvc_usb_topology_*`。

当前工程判断：这不是 PC 页面独占，也不是共享预览多人观看导致的独占；首帧阻塞更具体地收敛为
DV20 UVC 当前挂在 12M full-speed USB 拓扑并出现 STREAMON I/O error。下一步应换高速 USB 口/线、
减少转接、确认 5V 供电或使用 powered hub/known-good UVC 后再复测。

## 2026-07-03 camera USB recovery smoke tool

新增 `onboard/scripts/camera_usb_recovery_smoke.py`，用于换 USB 口/线、带供电 Hub 或
known-good UVC 后快速复测真实首帧。脚本只触碰相机 USB 和相机服务，不打开 WAVE ROVER
`/dev/ttyS5`，不发布 `/cmd_vel`，不执行 Nav2/manual/keyboard/free-roam/delivery。

脚本动作：

- 停止 `trashbot-local-webrtc-camera.service`，避免共享预览占用设备。
- 将目标 USB 设备与 root hub 的 `power/control` 置为 `on`，排除 autosuspend 干扰。
- 默认记录 `uvcvideo` 模块参数，并把 `/sys/module/uvcvideo/parameters/quirks` 复位到 `0`；
  需要保守复测时可显式传 `--skip-uvc-quirks-reset`。
- 可选 reauthorize 目标 USB 设备，模拟重新插拔。
- 解绑同一复合设备的 `snd-usb-audio` 接口，排除 full-speed 总线上音频接口干扰。
- 用 `v4l2-ctl` 对 `YUYV@320x240@20` 和 `MJPG@480x320@30` 做直接 STREAMON，并以输出文件
  大于 0 作为真实出帧证据。
- 最后重启相机服务，并输出 `trashbot.camera_usb_recovery_smoke.v1` JSON。

2026-07-03 07:30 CST 真机复测：脚本输出 `status=streamon_failed`、
`frame_observed=false`，两项 stream 均 `bytes=0` 且 `streamon_error=true`。因此当前画面缺口
仍是 DV20 UVC/USB 高速链路或设备本体问题，不是 PC 多页面预览独占，也不是 ROS2 地图或雷达问题。

2026-07-03 23:12 CST 继续复核当前上位机：恢复前 `uvcvideo quirks=4294967295`，
停止 `trashbot-local-webrtc-camera.service` 后确认 `/dev/video1` 无 owner；当前 quirks 下
`MJPG@640x480`、`MJPG@1280x720`、`YUYV@320x240` 全部 0 字节。随后把 quirks 写回 `0`、
只 reauthorize DV20 所在 USB 设备 `3-1` 后复测，同三组格式仍全部 0 字节，服务恢复为 active。
结论保持：这不是浏览器独占，也不是当前已知 UVC quirk 参数能修好的问题；恢复脚本新增 quirk 复位只是为了
让后续现场复测从干净 UVC 参数开始，并把 `uvc_quirks_before/after` 写入 JSON 证据。
